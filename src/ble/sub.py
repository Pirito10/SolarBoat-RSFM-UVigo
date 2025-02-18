# LIBRERIAS
import threading
import sys
import signal
import time
import serial
from flask import Flask, Response
import os
import json
 
# VARIABLES DEL SERVER FLASK
app = Flask(__name__)
server_running = True
 
# VARIABLES GLOBALES
total_sensor_bytes_received = 0
sensor_data = {
    "distance": None,
    "acceleration": None,
    "gyroscope": None,
    "compass": None,
    "angle_north_x": None,
    "angle_north_proj_x": None,
    "hora": None,
}
 
# **********************************************************************
# ************* CONFIGURACION PARA BLE ESCUCHAR LOS DATOS **************
# **********************************************************************
ble_port = '/dev/rfcomm0'
ble_baudrate = 9600
ble_connection = None
 
# Esperar hasta que el puerto esté disponible
def wait_for_ble_connection():
    global ble_connection
    while not os.path.exists(ble_port):
        print(f"Esperando a que {ble_port} esté disponible...")
        time.sleep(1)
    try:
        ble_connection = serial.Serial(ble_port, ble_baudrate, timeout=1)
        print(f"Conexión BLE establecida en {ble_port}")
    except serial.SerialException as e:
        print(f"Error al conectar con {ble_port}: {e}")
        ble_connection = None
 
# LECTURA DE DATOS DESDE BLE
def read_ble_data():
    while ble_connection and ble_connection.is_open:
        try:
            line = ble_connection.readline().decode('utf-8').strip()
            if line:
                print(f"Dato recibido por BLE: {line}")
                process_ble_data(line)
        except Exception as e:
            print(f"Error al leer desde BLE: {e}")
 
# Procesa cada línea recibida por BLE
def process_ble_data(line):
    global sensor_data, total_sensor_bytes_received
    try:
        total_sensor_bytes_received += len(line.encode('utf-8'))
        if "Distancia:" in line:
            sensor_data["distance"] = line.split(":")[1].strip()
        elif "Aceleración:" in line:
            sensor_data["acceleration"] = line.split(":")[1].strip()
        elif "Giroscopio:" in line:
            sensor_data["gyroscope"] = line.split(":")[1].strip()
        elif "Compás:" in line:
            sensor_data["compass"] = line.split(":")[1].strip()
        elif "Ángulo (norte y eje X):" in line:
            sensor_data["angle_north_x"] = line.split(":")[1].strip()
        elif "Ángulo (norte y proyección eje X):" in line:
            sensor_data["angle_north_proj_x"] = line.split(":")[1].strip()
 
            # Enviamos ACK cuando se reciba el último paquete
            send_acknowledgment("ACK")
    except Exception as e:
        print(f"Error procesando el dato: {e}")
 
# **************************************************************************
# **************************************************************************
# **************************************************************************
 
# **********************************************************************
# ************* CONFIGURACION PARA BLE ENVIAR LOS DATOS ****************
# **********************************************************************
def send_acknowledgment(message):
    if ble_connection and ble_connection.is_open:
        try:
            ble_connection.write((message + '\n').encode('utf-8'))
            print(f"ACK enviado: {message}")
        except Exception as e:
            print(f"Error al enviar ACK: {e}")
 
# **************************************************************************
# **************************************************************************
# **************************************************************************
 
# CAPTURA DEL BW DE LOS SENSORES
def monitor_sensor_bandwidth(interval=5):
    global total_sensor_bytes_received
    while True:
        time.sleep(interval)
        # Convertir a bits por segundo
        bandwidth_bps = (total_sensor_bytes_received * 8) / interval
        print("------------------------------------------------")
        print(f"Ancho de banda promedio de sensores: {bandwidth_bps:.2f} bps")
        print("------------------------------------------------")
        total_sensor_bytes_received = 0  # Reiniciar el contador
 
#******************************************************************#
#*************************** CTR+C ********************************#
#******************************************************************#
def signal_handler(sig, frame):
    """Manejador de señal para SIGINT (Ctrl+C)."""
    print("Ctrl+C detectado. Cerrando conexión BLE y servidor Flask...")
    if ble_connection and ble_connection.is_open:
        ble_connection.close()
    print("Servidor Flask cerrado correctamente.")
    sys.exit(0)
 
signal.signal(signal.SIGINT, signal_handler)
 
#******************************************************************#
#*************************** FLASK *******************************#
#******************************************************************#
@app.route('/')
def index():
    return '''
        <html>
            <head>
                <title>BLE Sensor Data</title>
            </head>
            <body>
                <h1>BLE Sensor Data</h1>
                <p>Consulta los datos de los sensores en <a href="/sensorData">/sensorData</a></p>
            </body>
        </html>
    '''
 
@app.route('/sensorData', methods=['GET'])
def get_sensor_data():
    if any(sensor_data.values()):
        cleaned_data = {
            k: (v.replace("\u00b0", "°") if isinstance(v, str) else v)
            for k, v in sensor_data.items()
        }
        return Response(json.dumps(cleaned_data, ensure_ascii=False),
                        content_type="application/json; charset=utf-8", status=200)
    else:
        return Response(json.dumps({"message": "No data received yet"}, ensure_ascii=False),
                        content_type="application/json; charset=utf-8", status=404)
                         
#******************************************************************#
#****************************** MAIN ******************************#
#******************************************************************#
if __name__ == '__main__':
    wait_for_ble_connection()  # Esperar hasta que el puerto esté disponible
    ble_thread = threading.Thread(target=read_ble_data, daemon=True)
    ble_thread.start()  # Iniciar el hilo de lectura de datos
 
    # Hilo para monitorear el ancho de banda
    bandwidth_thread = threading.Thread(target=monitor_sensor_bandwidth, daemon=True)
    bandwidth_thread.start()
 
 
    app.run(debug=False, host='0.0.0.0', port=80)