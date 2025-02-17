import sys
import time
import gpiozero
import serial
 
arduino_port = '/dev/ttyUSB0'  # Puerto serie del Arduino
lora_port = '/dev/ttyUSB1'  # Puerto serie del módulo LoRaWAN
arduino_baudrate = 9600  # Frecuencia del Arduino
lora_baudrate = 115200  # Frecuencia del módulo LoRaWAN
timeout = 1
  
# Inicializar conexión serial con el Arduino
try:
    arduino_serial = serial.Serial(arduino_port, arduino_baudrate, timeout=timeout)
    print(f"Conexión serial exitosa en {arduino_port}")
except serial.SerialException:
    arduino_serial = None
    print(f"No se pudo conectar al puerto serie {arduino_port}")
  
# Inicializar conexión serial con el módulo LoRaWAN
try:
    lora_serial = serial.Serial(lora_port, lora_baudrate, timeout=timeout)
    print(f"Conexión serial exitosa en {lora_port}\n")
except serial.SerialException:
    print(f"No se pudo conectar al puerto serie {lora_port}")
    sys.exit(1)
  
time.sleep(2)  # Asegurar que las conexiones seriales estén listas
  
# Diccionario para almacenar los datos más recientes
data = {
    "Temperatura": "0",
    "Distancia": "0",
    "Aceleración": "0,0,0",
    "Giroscopio": "0,0,0",
    "Compás": "0,0,0",
    "Heading": "0",
    "TiltHeading": "0",
}
  
# Función para formatear el payload
def format_payload(data):
    try:
        payload = f"{data['Temperatura']};{data['Distancia']};{data['Aceleración']};{data['Giroscopio']};{data['Compás']};{data['Heading']};{data['TiltHeading']}"
        return payload
    except Exception as e:
        print(f"Error al formatear datos: {e}")
        return "0;0;0,0,0;0,0,0;0,0,0;0;0"  # Enviar ceros en caso de error
     
# Obtener la temperatura de la CPU
def get_cpu_temperature():
    try:
        cpu = gpiozero.CPUTemperature()
        return f"{cpu.temperature:.2f}"  # Retornar la temperatura con dos decimales
    except Exception as e:
        print(f"Error al obtener la temperatura de la CPU: {e}")
        return "0"
  
# Leer datos continuamente del Arduino
def read_arduino_data():
    global data
    try:
        if arduino_serial and arduino_serial.in_waiting > 0:
            line = arduino_serial.readline().decode('utf-8').strip()
  
            # Procesar línea y actualizar el diccionario de datos
            if "Distancia:" in line:
                data["Distancia"] = line.split(":")[1].strip()
            elif "Aceleración (g) en X, Y, Z:" in line:
                data["Aceleración"] = line.split(":")[1].strip()
            elif "Giroscopio (grados/s) en X, Y, Z:" in line:
                data["Giroscopio"] = line.split(":")[1].strip()
            elif "Compás en X, Y, Z:" in line:
                data["Compás"] = line.split(":")[1].strip()
            elif "El ángulo en sentido horario entre el norte magnético y el eje X:" in line:
                data["Heading"] = line.split(":")[1].strip()
            elif "El ángulo en sentido horario entre el norte magnético y la proyección del eje X positivo en el plano horizontal:" in line:
                data["TiltHeading"] = line.split(":")[1].strip()
    except Exception as e:
        print(f"Error al leer datos del Arduino: {e}")
  
# Bucle principal
try:
    last_sent_time = time.time()  # Tiempo de la última vez que se envió un comando AT
  
    while True:
        # Actualizar la temperatura de la CPU
        data["Temperatura"] = get_cpu_temperature()
 
        # Leer datos continuamente del Arduino
        read_arduino_data()
  
        # Verificar si han pasado 5 segundos desde el último envío
        current_time = time.time()
        if current_time - last_sent_time >= 5:
            # Formatear los datos en el payload
            payload = format_payload(data)
  
            # Enviar payload al módulo LoRaWAN como comando AT
            at_command = f"AT+SendStr={payload}"
            lora_serial.write(at_command.encode('utf-8'))
            print(f"Comando enviado al módulo LoraWAN: {at_command}\n")
  
            # Actualizar el tiempo de la última vez que se envió el comando
            last_sent_time = current_time
  
except KeyboardInterrupt:
    print("Programa interrumpido por el usuario")
  
finally:
    # Cerrar las conexiones seriales
    if arduino_serial:
        arduino_serial.close()
    lora_serial.close()
    print("Conexiones seriales cerradas")