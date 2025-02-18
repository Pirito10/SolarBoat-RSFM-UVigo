# LIBRERIAS
import cv2
import threading, sys, signal, time
import numpy as np
import paho.mqtt.client as mqtt
import sqlite3
from sqlite3 import Error
from flask import Flask, jsonify, render_template, Response
   
# VARIABLES DEL SERVER FLASK
app = Flask(__name__)
server_running = True
flask_server = None
   
# VARIABLES GLOBALES
BROKER_DOMAIN = "domain.dyndns.org"
BROKER_PORT = 1883
dataReceived = {}
dataServer = "Datos del servidor"
latest_frame = None
topicVideo = 'video/stream'
topicStop = "barco/stop"
 
# CONFIGURACIÓN DE BASE DE DATOS
DATABASE = "sensor_database.db"
 
#******************************************************************#
#************************ MySQL/MariaDB ***************************#
#******************************************************************#
def create_connection():
    """Crear conexión con la base de datos SQLite"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        print("Conexión a SQLite establecida")
    except Error as e:
        print(f"Error al conectar a SQLite: {e}")
    return conn
 
# CREAR TABLA SI ESTA NO EXISTE:
def create_table():
    """Crear las tablas necesarias"""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS sensor_data (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                    temperature TEXT,
                                    distance TEXT,
                                    acceleration TEXT,
                                    gyroscope TEXT,
                                    compass TEXT,
                                    heading TEXT,
                                    tilt_heading TEXT);""")
            conn.commit()
            print("Tabla sensor_data creada o ya existente")
        except Error as e:
            print(f"Error al crear la tabla: {e}")
        finally:
            conn.close()
    else:
        print("No se pudo establecer la conexión con la base de datos.")
 
# # FUNCIONES PARA INSERTAR CADA DATO INDIVIDUALMENTE
def insert_temperature(temperature):
    """Insertar temperatura en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (temperature) VALUES (?)
            """, (temperature,))
            conn.commit()
            print("Temperatura insertada correctamente")
        except Error as e:
            print(f"Error al insertar temperatura: {e}")
        finally:
            conn.close()
 
 
def insert_distance(distance):
    """Insertar distancia en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (distance) VALUES (?)
            """, (distance,))
            conn.commit()
            print("Distancia insertada correctamente")
        except Error as e:
            print(f"Error al insertar distancia: {e}")
        finally:
            conn.close()
 
 
import json
 
 
def insert_acceleration(acceleration):
    """Insertar aceleración en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (acceleration) VALUES (?)
            """, (acceleration,))
            conn.commit()
            print("Aceleración insertada correctamente")
        except Error as e:
            print(f"Error al insertar aceleración: {e}")
        finally:
            conn.close()
 
 
def insert_gyroscope(gyroscope):
    """Insertar giroscopio en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (gyroscope) VALUES (?)
            """, (gyroscope,))
            conn.commit()
            print("Giroscopio insertado correctamente")
        except Error as e:
            print(f"Error al insertar giroscopio: {e}")
        finally:
            conn.close()
 
 
def insert_compass(compass):
    """Insertar compás en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (compass) VALUES (?)
            """, (compass,))
            conn.commit()
            print("Compás insertado correctamente")
        except Error as e:
            print(f"Error al insertar compás: {e}")
        finally:
            conn.close()
 
 
def insert_heading(heading):
    """Insertar heading en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (heading) VALUES (?)
            """, (heading,))
            conn.commit()
            print("Heading insertado correctamente")
        except Error as e:
            print(f"Error al insertar heading: {e}")
        finally:
            conn.close()
 
 
def insert_tilt_heading(tilt_heading):
    """Insertar tilt heading en la base de datos"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (tilt_heading) VALUES (?)
            """, (tilt_heading,))
            conn.commit()
            print("Tilt Heading insertado correctamente")
        except Error as e:
            print(f"Error al insertar tilt heading: {e}")
        finally:
            conn.close()
 
  
#******************************************************************#
#**************************** MQTT ********************************#
#******************************************************************#
client = mqtt.Client()
   
# VARIABLES PARA ALMACENAR LOS DATOS DE LOS SENSORES
temp_sensor_data_MQTT = None
dist_sensor_data_MQTT = None
accel_sensor_data_MQTT = None
gyroscope_sensor_data_MQTT = None
compass_sensor_data_MQTT = None
heading_sensor_data_MQTT = None
tiltHeading_sensor_data_MQTT = None
   
# LISTA DE TOPICOS MQTT PARA LOS DATOS DE LOS SENSORES
TOPICS = {
    'sensor/temperature/MQTT': 'temp_sensor_data_MQTT',
    'sensor/distance/MQTT': 'dist_sensor_data_MQTT',
    'sensor/acceleration/MQTT': 'accel_sensor_data_MQTT',
    'sensor/gyroscope/MQTT': 'gyroscope_sensor_data_MQTT',
    'sensor/compass/MQTT': 'compass_sensor_data_MQTT',
    'sensor/heading/MQTT': 'heading_sensor_data_MQTT',
    'sensor/tilt_heading/MQTT': 'tiltHeading_sensor_data_MQTT',
}
   
# FUNCION PARA MANEJAR LA CONEXION A MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conectado al broker MQTT")
   
        client.subscribe(topicVideo)
           
        for topic in TOPICS.keys():
            client.subscribe(topic)
            print(f"Suscrito al topico: {topic}")
    else:
        print(f"Error al conectarse al broker MQTT. Código de error: {rc}")
   
# FUNCION PARA PROCESAR LOS MENSAJES RECIBIDOS DE MQTT
def on_message(client, userdata, msg):
    global temp_sensor_data_MQTT, dist_sensor_data_MQTT, accel_sensor_data_MQTT
    global gyroscope_sensor_data_MQTT, compass_sensor_data_MQTT, heading_sensor_data_MQTT
    global tiltHeading_sensor_data_MQTT
   
    global latest_frame
    topic = msg.topic
       
    # VERIFICACION SI EL TOPICO ES DE VIDEO
    if topic == topicVideo:
        nparr = np.frombuffer(msg.payload, np.uint8)
        latest_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print("Frame de video recibido a través de MQTT")
   
    else:
        # PROCESADO DE DATOS
        payload = msg.payload.decode('utf-8')
   
        # ASIGNAMOS EL DATO A LA VARIABLE CORRESPONDIENTE
        if topic == 'sensor/temperature/MQTT':
            temp_sensor_data_MQTT = payload
            print(f"Temperatura: {temp_sensor_data_MQTT}")
            insert_temperature(temp_sensor_data_MQTT)
 
            # ALARMA AUTOMATICA
            if float(temp_sensor_data_MQTT) > 55:
                print("Temperatura elevada.")
                client.publish(topicStop, "STOP")
             
  
        elif topic == 'sensor/distance/MQTT':
            dist_sensor_data_MQTT = payload
            insert_distance(dist_sensor_data_MQTT)
            print(f"Distancia: {dist_sensor_data_MQTT}")
        elif topic == 'sensor/acceleration/MQTT':
            accel_sensor_data_MQTT = payload
            insert_acceleration(accel_sensor_data_MQTT)
            print(f"Aceleración: {accel_sensor_data_MQTT}")
        elif topic == 'sensor/gyroscope/MQTT':
            gyroscope_sensor_data_MQTT = payload
            insert_gyroscope(gyroscope_sensor_data_MQTT)
            print(f"Giroscopio: {gyroscope_sensor_data_MQTT}")
        elif topic == 'sensor/compass/MQTT':
            compass_sensor_data_MQTT = payload
            insert_compass(compass_sensor_data_MQTT)
            print(f"Compás: {compass_sensor_data_MQTT}")
        elif topic == 'sensor/heading/MQTT':
            heading_sensor_data_MQTT = payload
            insert_heading(heading_sensor_data_MQTT)
            print(f"Heading: {heading_sensor_data_MQTT}")
        elif topic == 'sensor/tilt_heading/MQTT':
            tiltHeading_sensor_data_MQTT = payload
            insert_tilt_heading(tiltHeading_sensor_data_MQTT)
            print(f"Tilt Heading: {tiltHeading_sensor_data_MQTT}")
   
# FUNCION PARA INICIAR EL CLIENTE MQTT
def start_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_DOMAIN, BROKER_PORT)
    client.loop_start()
   
#******************************************************************#
#******************************************************************#
#******************************************************************#
   
# ENVIO DEL VIDEO
def generate_video():
    global latest_frame
    while True:
        if latest_frame is not None:
            # Reduce la resolución de los fotogramas antes de transmitirlos
            img_resized = cv2.resize(latest_frame, (320, 240))
            ret, jpeg = cv2.imencode('.jpg', img_resized, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret:
                frame = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        time.sleep(0.05)
   
# CAPTURA DEL BW DE VIDEO STREAMING
total_bytes_transmitted = 0
def monitor_bandwidth(interval=5):
    global total_bytes_transmitted
    while True:
        time.sleep(interval)
        # Convertir a bits por segundo
        bandwidth_bps = (total_bytes_transmitted * 8) / interval
        print(f"Ancho de banda promedio: {bandwidth_bps:.2f} bps")
        total_bytes_transmitted = 0
   
# Hilo para ejecutar la monitorizacion
bandwidth_thread = threading.Thread(target=monitor_bandwidth)
bandwidth_thread.start()
   
#******************************************************************#
#*************************** CTR+C ********************************#
#******************************************************************#
def signal_handler(sig, frame):
    """Manejador de señal para SIGINT (Ctrl+C)."""
    print("Ctrl+C detectado. Cerrando suscriptores y servidor Flask...")
   
    if client is not None and client.is_connected():
        print("Cerrando cliente MQTT...")
        client.disconnect()
    if zenoh_session is not None:
        print("Cerrando sesión Zenoh...")
        zenoh_session.close()
   
    print("Servidor Flask cerrado correctamente.")
    sys.exit(0)
   
#******************************************************************#
#*************************** INICIO *******************************#
#******************************************************************#
@app.route('/')
def dashboard():
    return render_template('dashboard_secciones.html')
  
#******************************************************************#
#****************************** GET *******************************#
#******************************************************************#
@app.route('/serverData', methods=['GET'])
def getServerData():
    response = {
        "message": "Datos recibidos exitosamente",
        "data": dataServer
    }
    return jsonify(response), 200
   
@app.route('/database')
def show_combined_data():
    """Obtener los 100 últimos datos independientes de cada sensor y combinarlos en columnas"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
 
            # Consultas independientes para los 100 últimos datos de cada tipo
            query_temperature = "SELECT temperature FROM sensor_data WHERE temperature IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_distance = "SELECT distance FROM sensor_data WHERE distance IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_acceleration = "SELECT acceleration FROM sensor_data WHERE acceleration IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_gyroscope = "SELECT gyroscope FROM sensor_data WHERE gyroscope IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_compass = "SELECT compass FROM sensor_data WHERE compass IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_heading = "SELECT heading FROM sensor_data WHERE heading IS NOT NULL ORDER BY id DESC LIMIT 100"
            query_tilt_heading = "SELECT tilt_heading FROM sensor_data WHERE tilt_heading IS NOT NULL ORDER BY id DESC LIMIT 100"
 
            # Ejecución de consultas
            temperature_data = [row[0] for row in cursor.execute(query_temperature).fetchall()]
            distance_data = [row[0] for row in cursor.execute(query_distance).fetchall()]
            acceleration_data = [row[0] for row in cursor.execute(query_acceleration).fetchall()]
            gyroscope_data = [row[0] for row in cursor.execute(query_gyroscope).fetchall()]
            compass_data = [row[0] for row in cursor.execute(query_compass).fetchall()]
            heading_data = [row[0] for row in cursor.execute(query_heading).fetchall()]
            tilt_heading_data = [row[0] for row in cursor.execute(query_tilt_heading).fetchall()]
 
            # Combinar los datos en un diccionario para enviar a la plantilla
            combined_data = {
                "temperature": temperature_data,
                "distance": distance_data,
                "acceleration": acceleration_data,
                "gyroscope": gyroscope_data,
                "compass": compass_data,
                "heading": heading_data,
                "tilt_heading": tilt_heading_data
            }
 
            return render_template('combined_data.html', combined_data=combined_data, enumerate=enumerate)
 
        except Error as e:
            return jsonify({"error": f"Error al obtener datos combinados: {e}"}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
 
 
@app.route('/database/<sensor_type>')
def show_sensor_data(sensor_type):
    """Obtener los datos con timestamp para un sensor específico"""
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
 
            # Diccionario para mapear el sensor_type al campo de la base de datos
            sensor_mapping = {
                "temperature": "temperature",
                "distance": "distance",
                "acceleration": "acceleration",
                "gyroscope": "gyroscope",
                "compass": "compass",
                "heading": "heading",
                "tilt_heading": "tilt_heading",
            }
 
            # Verificar que el sensor solicitado existe
            if sensor_type not in sensor_mapping:
                return jsonify({"error": "Tipo de sensor no válido"}), 400
 
            # Consultar los datos para el sensor solicitado
            sensor_column = sensor_mapping[sensor_type]
            query = f"""
                SELECT timestamp, {sensor_column}
                FROM sensor_data
                WHERE {sensor_column} IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT 100;
            """
 
            sensor_data = cursor.execute(query).fetchall()
 
            # Renderizar la plantilla
            return render_template(
                'sensor_data_individual.html',
                sensor_type=sensor_type,
                sensor_data=sensor_data
            )
 
        except Error as e:
            return jsonify({"error": f"Error al obtener datos: {e}"}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
 
 
 
#******************************************************************#
#*************** DATOS DE LOS SENSORES POR MQTT *******************#
#******************************************************************#
@app.route('/mqttSensorData')
def get_mqtt_sensor_data():
    sensor_data = jsonify({
        "temperature": temp_sensor_data_MQTT,
        "distance": dist_sensor_data_MQTT,
        "acceleration": accel_sensor_data_MQTT,
        "gyroscope": gyroscope_sensor_data_MQTT,
        "compass": compass_sensor_data_MQTT,
        "heading": heading_sensor_data_MQTT,
        "tiltHeading": tiltHeading_sensor_data_MQTT
    })
   
    if all([temp_sensor_data_MQTT, dist_sensor_data_MQTT, accel_sensor_data_MQTT, gyroscope_sensor_data_MQTT,
            compass_sensor_data_MQTT, heading_sensor_data_MQTT, tiltHeading_sensor_data_MQTT]):
        return sensor_data
    else:
        return jsonify({"message": "No data received yet"}), 404
   
#******************************************************************#
#************* DATOS DEL VIDEO ENVIADO POR MQTT *******************#
#******************************************************************#
@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')
   
#******************************************************************#
#******************** BOTON MANUAL AL BARCO ***********************#
#******************************************************************#
@app.route('/stop', methods=['POST'])
def stop():
    # PUBLICAMOS LA ALERTA
    client.publish(topicStop, "STOP")
  
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mensaje enviado</title>
        </head>
        <body style="text-align: center; font-family: Arial, sans-serif; margin-top: 50px;">
            <h1>¡Mensaje enviado al barco!</h1>
            <a href="/" style="text-decoration: none; font-size: 20px; color: blue;">Volver</a>
        </body>
        </html>
    '''
  
#******************************************************************#
#****************************** MAIN ******************************#
#******************************************************************#
if __name__ == '__main__':
    try:
        create_table()
 
        # Iniciar la simulación de datos aleatorios
        print("Iniciando simulación de datos aleatorios...")
        simulation_thread = threading.Thread(target=simulate_data, args=(5,), daemon=True)
        simulation_thread.start()
 
        start_mqtt()
        app.run(debug=False, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)