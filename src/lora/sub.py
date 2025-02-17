import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template
import sys
import base64
import json
from datetime import datetime
import time

# Configuración del broker MQTT y del tópico
BROKER = "eu1.cloud.thethings.network"
PORT = 1883
USERNAME = "rsfm-lora-2425@ttn"
PASSWORD = "NNSXS.QYOXP5QLW23WRRWKNWTARMGPK7VJ6NJZAZOHJ4Y.5K5KX2MQMGXYAGTPD7CNXNALQ55JRHP6TXZX6P6KQB3GB44ZFBJA"
APPLICATION_ID = "rsfm-lora-2425"
TENANT_ID = "ttn"
DEVICE_ID = "rsfm-lora"
TOPIC = "v3/" + APPLICATION_ID + "@" + TENANT_ID + "/devices/" + DEVICE_ID + "/up"
 
# Configuración del servidor Flask
app = Flask(__name__)
dataReceived = {}
 
# Función para procesar mensajes MQTT
def process_mqtt_message(msg):
    try:
        # Obtener el tiempo actual en milisegundos
        current_time_ms = int(time.time() * 1000)

        # Cargar el mensaje JSON
        payload_json = json.loads(msg.payload.decode('utf-8'))

        # Extraer el payload en Base64
        base64_payload = payload_json["uplink_message"]["frm_payload"]

        # Decodificar el payload Base64 a bytes
        decoded_bytes = base64.b64decode(base64_payload)

        # Convertir los bytes a string
        decoded_string = decoded_bytes.decode('utf-8')

        # Separar los datos por punto y coma
        data_parts = decoded_string.split(";")

        # Procesar los datos según el formato esperado
        processed_data = {
            "temperature": float(data_parts[0]),
            "distance": float(data_parts[1]),
            "acceleration": list(map(float, data_parts[2].split(","))),
            "gyroscope": list(map(float, data_parts[3].split(","))),
            "compass": list(map(float, data_parts[4].split(","))),
            "heading": float(data_parts[5]),
            "tilt_heading": float(data_parts[6])
        }

        # Obtener el timestamp del servidor TTN (campo "received_at")
        received_at_iso = payload_json["uplink_message"]["received_at"]
        received_at = datetime.fromisoformat(received_at_iso.replace("Z", "+00:00"))  # Convertir a datetime
        received_at_ms = int(received_at.timestamp() * 1000)  # Convertir a milisegundos

        # Calcular la latencia
        latency_ms = (current_time_ms - received_at_ms) / 1000

        processed_data["latency"] = latency_ms
        return processed_data

    except Exception as e:
        print(f"Error al procesar el mensaje MQTT: {e}")
        return None
 
# Callback para conexión exitosa
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Conexión exitosa al broker MQTT")
        client.subscribe(TOPIC)
    else:
        print(f"Error en la conexión: {rc}")
        
# Callback para recibir mensajes
def on_message(client, userdata, msg):
    global dataReceived
    processed_data = process_mqtt_message(msg)
    if processed_data:
        print("Datos recibidos y procesados:", processed_data)
        dataReceived = processed_data
 
# Configuración del cliente MQTT
def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()
    return client

# Endpoints del servidor Flask
@app.route('/')
def dashboard():
    return render_template('dashboard_secciones.html')

@app.route('/sensorData', methods=['GET'])
def get_sensor_data():
    if dataReceived:
        return jsonify(dataReceived), 200
    else:
        return jsonify({"message": "No data received yet"}), 404

# Función principal
if __name__ == '__main__':
    try:
        mqtt_client = start_mqtt()
        app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)
    except KeyboardInterrupt:
        print("Deteniendo servidor...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        sys.exit(0)