import bluetooth
import gpiozero
import serial
import time

# Dirección MAC del servidor BLE (Raspberry Pi A)
SERVER_MAC = "B8:27:EB:7D:8C:DE"
PORT = 1
 
# DEFINICION DE CONSTANTES
DISTANCIA = "Distancia:"
ACELERACION = "Aceleración (g) en X, Y, Z:"
GIROSCOPIO = "Giroscopio (grados/s) en X, Y, Z:"
COMPAS = "Compás en X, Y, Z:"
ANGULO_NORTE_X = "El ángulo en sentido horario entre el norte magnético y el eje X:"
ANGULO_NORTE_PROYECCION_X = "El ángulo en sentido horario entre el norte magnético y la proyección del eje X positivo en el plano horizontal:"
 
ser = None
latencia_start = None
 
# **********************************************************************
# ************* CONFIGURACION PARA BLE ENVIAR LOS DATOS ****************
# **********************************************************************
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
 
# INICIALIZAR LA CONEXION SERIAL BLUETOOTH
def init_bluetooth_connection():
    global ser
    bluetooth_port = '/dev/rfcomm0'  # Ajusta este puerto según tu configuración
    baud_rate = 9600
    timeout_sec = 2
 
    try:
        ser = serial.Serial(bluetooth_port, baud_rate, timeout=timeout_sec)
        print("Conexión Bluetooth exitosa")
    except serial.SerialException:
        print("No se pudo conectar al dispositivo Bluetooth. Verifica el puerto y el emparejamiento.")
        return None
 
# LEER DATOS DEL BLUETOOTH Y DEVOLVERLOS COMO UNA LISTA
def read_sensor_data():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            return line
    except Exception as e:
        print(f"Error al leer datos: {e}")
        return None
 
# Enviar datos por Bluetooth
def send_data_bluetooth(client_sock, temperatura, lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading):
    global latencia_start
 
    try:
        #mensaje = f"Temperatura: {temperatura}°C\n"
        #client_sock.send(mensaje + "\n")
 
        if lineDistance is not None:
            mensaje = f"Distancia: {lineDistance} cm"
            print(f"Enviando por Bluetooth: {mensaje}")
            client_sock.send(mensaje + "\n")
 
        elif lineAcceleration is not None:
            mensaje = f"Aceleración: {lineAcceleration}"
            print(f"Enviando por Bluetooth: {mensaje}")
            client_sock.send(mensaje + "\n")
 
        elif lineGyroscope is not None:
            mensaje = f"Giroscopio: {lineGyroscope}"
            print(f"Enviando por Bluetooth: {mensaje}")
            client_sock.send(mensaje + "\n")
 
        elif lineCompass is not None:
            mensaje = f"Compás: {lineCompass}"
            print(f"Enviando por Bluetooth: {mensaje}")
            client_sock.send(mensaje + "\n")
 
        elif lineaHeading is not None:
            mensaje = f"Ángulo (norte y eje X): {lineaHeading}°"
            print(f"Enviando por Bluetooth: {mensaje}")
            client_sock.send(mensaje + "\n")
 
        elif lineTiltHeading is not None:
            mensaje = f"Ángulo (norte y proyección eje X): {lineTiltHeading}°"
            print(f"Enviando por Bluetooth: {mensaje}")
            latencia_start = time.time()
            client_sock.send(mensaje + "\n")
 
            if not receive_ack(client_sock):
                print("ACK no recibido para Ángulo (norte y proyección eje X)")
 
    except Exception as e:
        print(f"Error al enviar datos: {e}")
 
# **********************************************************************
# **********************************************************************
# **********************************************************************
 
# **********************************************************************
# ************* CONFIGURACION PARA BLE ESCUCHAR LOS DATOS **************
# **********************************************************************
def receive_ack(client_sock):
    global latencia_start
    try:
        # Esperar un mensaje del cliente
        ack_message = client_sock.recv(1024).decode('utf-8').strip()
        if ack_message == "ACK":
            print("ACK recibido")
            end_time = time.time()
            latencia = end_time - latencia_start
            print("--------------------------------------------")
            print(f"Latencia calculada: {latencia:.3f} segundos")
            print("--------------------------------------------")
            return True
        else:
            print(f"Mensaje inesperado recibido: {ack_message}")
            return False
    except Exception as e:
        print(f"Error al recibir ACK: {e}")
        return False
 
# **********************************************************************
# **********************************************************************
# **********************************************************************
         
#******************************************************************#
#****************************** MAIN ******************************#
#******************************************************************#
def main():
    #init_bluetooth_connection()
    init_serial_connection()
 
    # Crear socket Bluetooth
    client_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
 
    try:
        # Conectar al servidor Bluetooth
        client_sock.connect((SERVER_MAC, PORT))
        print("Conectado a", SERVER_MAC)
 
        while True:
 
            temperatura = getRaspData()
            line = read_sensor_data()
         
 
            # OBTENER LOS DATOS Y PROCESARLOS
            lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading = procesar_linea(line)
 
            # Preparar mensaje para enviar
            send_data_bluetooth(client_sock, temperatura, lineDistance, lineAcceleration, lineGyroscope, lineCompass, lineaHeading, lineTiltHeading)
   
    except OSError as e:
        print("Error:", e)
    finally:
        ser.close()
        client_sock.close()
 
if __name__ == '__main__':
    main()