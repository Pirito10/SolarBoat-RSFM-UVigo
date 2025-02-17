import paho.mqtt.client as mqtt
import gpiozero
import serial
import time
import sys, os
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

# CALCULO DE LA LATENCIA
ACK_TOPIC = "barco/ack"
latencia_start = None

# CONFIGURACION DEL CLIENTE MQTT
broker = "192.168.200.1"
port = 1883
client = mqtt.Client("SensorPublisher")

# CONEXION AL BROKER MQTT
def connect_mqtt():
    client.connect(broker, port)
    client.on_message = on_message  # Publicador de alertas
    client.subscribe("barco/stop")
    client.subscribe(ACK_TOPIC)
    client.loop_start()

# RECEPCION DE MENSAJES DE ALERTA
def on_message(client, userdata, msg):
    global alerta, latencia_start
    print("Mensaje recibido en " + msg.topic + ": " + msg.payload.decode())
    
    # PROCESAMOS LA ALARMA PROVENIENTE DEL SERVIDOR DE TIERRA
    if msg.topic == "barco/stop" and msg.payload.decode() == "STOP":
        print("\u00a1Programa detenido por el servidor!")
        alerta = True
        ser.close()
        client.loop_stop()
        client.disconnect()
        sys.exit(0)
    
    # PROCESAMOS EL MENSAJE DE CONFIRMACION PARA EL CALCULO DE LATENCIA
    if msg.topic == ACK_TOPIC:
        end_time = time.time()
        latencia = end_time - latencia_start
        print("--------------------------------------------")
        print("Latencia calculada: {:.3f} segundos".format(latencia))
        print("--------------------------------------------")

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
        print("Error al leer datos: " + str(e))
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
def publicData(lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading):
    global latencia_start

    if lineDistance is not None:
        print("Publicando distancia: " + str(lineDistance))
        client.publish("sensor/distance/MQTT", str(lineDistance))

    elif lineAcceleration is not None:
        print("Publicando aceleración: " + str(lineAcceleration))
        client.publish("sensor/acceleration/MQTT", str(lineAcceleration))

    elif lineGyroscope is not None:
        print("Publicando giroscopio: " + str(lineGyroscope))
        client.publish("sensor/gyroscope/MQTT", str(lineGyroscope))

    elif lineCompass is not None:
        print("Publicando compás: " + str(lineCompass))
        client.publish("sensor/compass/MQTT", str(lineCompass))

    elif lineaHeading is not None:
        print("Publicando ángulo (norte y eje X): " + str(lineaHeading))
        client.publish("sensor/heading/MQTT", str(lineaHeading))

    elif lineTiltHeading is not None:
        print("Publicando ángulo (norte y proyección eje X): " + str(lineTiltHeading))
        
        # INICIAMOS EL TEMPORIZADOR
        latencia_start = time.time()
        client.publish("sensor/tilt_heading/MQTT", str(lineTiltHeading))

# FUNCIONES DE PROCESAMIENTO DE SENSORES

def get_distance(line):
    if line and DISTANCIA in line:
        distance_str = line.split(":")[1].strip().replace("cm", "")
        return float(distance_str)
    return None

def get_acceleration(line):
    if line and ACELERACION in line:
        return line.split(":")[1].strip()
    return None

def get_gyroscope(line):
    if line and GIROSCOPIO in line:
        return line.split(":")[1].strip()
    return None

def get_compass(line):
    if line and COMPAS in line:
        return line.split(":")[1].strip()
    return None

def get_heading(line):
    if line and ANGULO_NORTE_X in line:
        return float(line.split(":")[1].strip())
    return None

def get_tilt_heading(line):
    if line and ANGULO_NORTE_PROYECCION_X in line:
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

            client.publish("sensor/temperature/MQTT", str(temperatura))
            time.sleep(1)

            lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading = procesar_linea(line)
            publicData(lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading)

    finally:
        ser.close()
        client.loop_stop()
        client.disconnect()
        sys.exit(1)

if __name__ == '__main__':
    main()