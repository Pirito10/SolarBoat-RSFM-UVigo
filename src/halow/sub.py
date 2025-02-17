# LIBRERIAS
import cv2
import threading, sys, signal, base64, time
import numpy as np
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify, render_template, Response

# VARIABLES DEL SERVER FLASK
app = Flask(__name__)
server_running = True
flask_server = None

# VARIABLES GLOBALES
total_sensor_bytes_received = 0
dataReceived = {}
dataServer = "Datos del servidor"
latest_frame = None
topicVideo = 'video/stream'
topicStop = "barco/stop"

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
            print("Suscrito al topico: " + topic)
    else:
        print("Error al conectarse al broker MQTT. Código de error: {}".format(rc))

# FUNCION PARA PROCESAR LOS MENSAJES RECIBIDOS DE MQTT
def on_message(client, userdata, msg):
    global temp_sensor_data_MQTT, dist_sensor_data_MQTT, accel_sensor_data_MQTT
    global gyroscope_sensor_data_MQTT, compass_sensor_data_MQTT, heading_sensor_data_MQTT
    global tiltHeading_sensor_data_MQTT

    global latest_frame, total_sensor_bytes_received
    topic = msg.topic

    # VERIFICACION SI EL TOPICO ES DE VIDEO
    if topic == topicVideo:
        nparr = np.frombuffer(msg.payload, np.uint8)
        latest_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print("Frame de video recibido a través de MQTT")

    else:
        # PROCESADO DE DATOS
        payload = msg.payload.decode('utf-8')

        # PARA CALCULAR EL BW DE LOS SENSORES
        total_sensor_bytes_received += len(payload)

        # ASIGNAMOS EL DATO A LA VARIABLE CORRESPONDIENTE
        if topic == 'sensor/temperature/MQTT':
            temp_sensor_data_MQTT = payload

            # ALARMA AUTOMATICA
            if float(temp_sensor_data_MQTT) > 55:
                print("Temperatura elevada.")
                client.publish(topicStop, "STOP")
            print("Temperatura: " + temp_sensor_data_MQTT)

        elif topic == 'sensor/distance/MQTT':
            dist_sensor_data_MQTT = payload
            print("Distancia: " + dist_sensor_data_MQTT)
        elif topic == 'sensor/acceleration/MQTT':
            accel_sensor_data_MQTT = payload
            print("Aceleración: " + accel_sensor_data_MQTT)
        elif topic == 'sensor/gyroscope/MQTT':
            gyroscope_sensor_data_MQTT = payload
            print("Giroscopio: " + gyroscope_sensor_data_MQTT)
        elif topic == 'sensor/compass/MQTT':
            compass_sensor_data_MQTT = payload
            print("Compás: " + compass_sensor_data_MQTT)
        elif topic == 'sensor/heading/MQTT':
            heading_sensor_data_MQTT = payload
            print("Heading: " + heading_sensor_data_MQTT)
        elif topic == 'sensor/tilt_heading/MQTT':
            tiltHeading_sensor_data_MQTT = payload
            print("Tilt Heading: " + tiltHeading_sensor_data_MQTT)
            
            # Enviamos un mensaje de confirmación al barco
            client.publish("barco/ack", "ACK")

# FUNCION PARA INICIAR EL CLIENTE MQTT
def start_mqtt():
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("192.168.200.1", 1883)
    client.loop_start()

#******************************************************************#
#********************** BW PARA VIDEO *****************************#
#******************************************************************#
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
        print("-------------------------------------------------------")
        print("Ancho de banda promedio del Video Streaming: {:.2f} bps".format(bandwidth_bps))
        print("-------------------------------------------------------")
        total_bytes_transmitted = 0

# Hilo para ejecutar la monitorizacion
bandwidth_thread = threading.Thread(target=monitor_bandwidth)
bandwidth_thread.start()

#******************************************************************#
#********************** BW PARA SENSORES **************************#
#******************************************************************#
def monitor_sensor_bandwidth(interval=10):
    global total_sensor_bytes_received
    while True:
        time.sleep(interval)
        # Convertir a bits por segundo
        bandwidth_bps = (total_sensor_bytes_received * 8) / interval
        print("---------------------------------------------------")
        print("Ancho de banda promedio de Sensores: {:.2f} bps".format(bandwidth_bps))
        print("---------------------------------------------------")
        total_sensor_bytes_received = 0 # Reiniciar el contador

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
        start_mqtt()
        sensor_bandwidth_thread = threading.Thread(target=monitor_sensor_bandwidth)
        sensor_bandwidth_thread.start()

        app.run(debug=False, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)