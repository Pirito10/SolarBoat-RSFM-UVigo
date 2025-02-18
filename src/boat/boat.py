import paho.mqtt.client as mqtt
import gpiozero
import serial
import time
import sys
 
import psutil
 
# DEFINICION DE CONSTANTES
DISTANCIA = "Distancia:"
ACELERACION = "Aceleración (g) en X, Y, Z:"
GIROSCOPIO = "Giroscopio (grados/s) en X, Y, Z:"
COMPAS = "Compás en X, Y, Z:"
ANGULO_NORTE_X = "El ángulo en sentido horario entre el norte magnético y el eje X:"
ANGULO_NORTE_PROYECCION_X = "El ángulo en sentido horario entre el norte magnético y la proyección del eje X positivo en el plano horizontal:"
 
ser = None
alerta = False
 
# CONFIGURACION DEL CLIENTE MQTT
BROKER_DOMAIN = "domain.dyndns.org"
BROKER_PORT = 1883
client = mqtt.Client("SensorPublisher")
 
# CONEXION AL BROKER MQTT
def connect_mqtt():
    client.connect(BROKER_DOMAIN, BROKER_PORT)
    client.on_message = on_message #Publicador de alertas
    client.subscribe("barco/stop")
    client.loop_start()
 
# RECEPCIÓN DE MENSAJES DE ALERTA:
def on_message(client, userdata, msg):
    global alerta
    print(f"Mensaje recibido en {msg.topic}: {msg.payload.decode()}")
    if msg.payload.decode() == "STOP":
        print("¡Programa detenido por el servidor!")
        alerta = True
        ser.close()
        client.loop_stop()
        client.disconnect()        # Cerrar puerto serial si está abierto
        sys.exit(0)
 
# LEER DATOS DE TEMPERATURA DE RASPI
def getRaspData():
    cpu = gpiozero.CPUTemperature()
    temp = cpu.temperature 
    return temp
 
# INICIALIZAR LA CONEXION SERIAL
def init_serial_connection():
    global ser
    arduino_port = '/dev/ttyUSB0'
    baud_rate = 9600
    timeout_sec = 2
 
    try:
        ser = serial.Serial(arduino_port, baud_rate, timeout=timeout_sec)
        print("Conexión exitosa con el Arduino")
    except serial.SerialException:
        print("No se pudo conectar al Arduino. Verifica el puerto y el cable.")
        return None
 
# LEER DATOS DEL ARDUINO Y DEVOLVERLOS COMO UNA LISTA
def read_sensor_data():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            return line
    except Exception as e:
        print(f"Error al leer datos: {e}")
        return None
 
# PROCESAR LINEA POR LINEA
def procesar_linea(line):
    distance = None
    acceleration = None
    gyroscope = None
    compass = None
    heading = None
    tilt_heading = None
 
    if line is None:
        line = " "
 
    if DISTANCIA in line:
        distance = get_distance(line)
    elif ACELERACION in line:
        acceleration = get_acceleration(line)
    elif GIROSCOPIO in line:
        gyroscope = get_gyroscope(line)
    elif COMPAS in line:
        compass = get_compass(line)
    elif ANGULO_NORTE_X in line:
        heading = get_heading(line)
    elif ANGULO_NORTE_PROYECCION_X in line:
        tilt_heading = get_tilt_heading(line)
 
    return distance, acceleration, gyroscope, compass, heading, tilt_heading
 
# PUBLICACION DE CADA VALOR EN SU CORRESPONDIENTE TOPICO
def publicData(lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading, start):
    if lineDistance is not None:
        print(f"Publicando distancia: {lineDistance}")
        client.publish("sensor/distance/MQTT", str(lineDistance))
 
    elif lineAcceleration is not None:
        print(f"Publicando aceleración: {lineAcceleration}")
        client.publish("sensor/acceleration/MQTT", str(lineAcceleration))
 
    elif lineGyroscope is not None:
        print(f"Publicando giroscopio: {lineGyroscope}")
        client.publish("sensor/gyroscope/MQTT", str(lineGyroscope))
 
    elif lineCompass is not None:
        print(f"Publicando compás: {lineCompass}")
        client.publish("sensor/compass/MQTT", str(lineCompass))
 
    elif lineaHeading is not None:
        print(f"Publicando ángulo (norte y eje X): {lineaHeading}")
        client.publish("sensor/heading/MQTT", str(lineaHeading))
 
    elif lineTiltHeading is not None:
        print(f"Publicando ángulo (norte y proyección eje X): {lineTiltHeading}")
        client.publish("sensor/tilt_heading/MQTT", str(lineTiltHeading))
 
        end = time.time()
        latencia = end - start
        print(f"Latencia: {latencia} secs")
 
# OBTENER DISTANCIA
def get_distance(line):
    if line and "Distancia:" in line:
        distance_str = line.split(":")[1].strip().replace("cm", "")
        return float(distance_str)
    return None
 
# OBTENER ACELERACION
def get_acceleration(line):
    if line and "Aceleración (g) en X, Y, Z:" in line:
        return line.split(":")[1].strip()
    return None
 
# OBTENER GIROSCOPIO
def get_gyroscope(line):
    if line and "Giroscopio (grados/s) en X, Y, Z:" in line:
        return line.split(":")[1].strip()
    return None
 
# OBTENER BRUJULA
def get_compass(line):
    if line and "Compás en X, Y, Z:" in line:
        return line.split(":")[1].strip()
    return None
 
# OBTENER HEADING
def get_heading(line):
    if line and "El ángulo en sentido horario entre el norte magnético y el eje X:" in line:
        return float(line.split(":")[1].strip())
    return None
 
# OBTENER TILTHEADING
def get_tilt_heading(line):
    if line and "El ángulo en sentido horario entre el norte magnético y la proyección del eje X positivo en el plano horizontal:" in line:
        return float(line.split(":")[1].strip())
    return None
 
# MAIN
def main():
    global alerta
    connect_mqtt()
    init_serial_connection()
 
    try:
        while not alerta:
            temperatura = getRaspData()
            line = read_sensor_data()
             
            start = time.time()
 
            #before
            before = psutil.net_io_counters()
 
            client.publish("sensor/temperature/MQTT", str(temperatura))
             
            time.sleep(1)
            
 
            # OBTENER LOS DATOS Y PROCESARLOS
            lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading = procesar_linea(line)
 
            # PUBLICACION DE DATOS
            publicData(lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading, start)
 
            #after
            after =  psutil.net_io_counters()
 
            sent_bytes = after.bytes_sent - before.bytes_sent
            received_bytes = after.bytes_recv - before.bytes_recv
 
    finally:
        ser.close()
        client.loop_stop()
        client.disconnect()        # Cerrar puerto serial si está abierto
        sys.exit(1)
 
if __name__ == '__main__':
    main()