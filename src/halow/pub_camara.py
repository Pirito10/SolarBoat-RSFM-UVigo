import cv2
import threading
import paho.mqtt.client as mqtt
import psutil
import time

# Inicializa los parámetros de MQTT y la cámara
def initialize_stream(topic, video_address=0, host="192.168.200.1", port=1883):
    client = mqtt.Client()  # Crear nueva instancia
    client.connect(host, port)

    cam = cv2.VideoCapture(video_address)
    if not cam.isOpened():
        print("Error: No se pudo acceder a la cámara o fuente de video en " + str(video_address))
        return None, None

    return client, cam

# Función para enviar los fotogramas al broker MQTT
def stream_video(client, cam, topic):
    print("Streaming desde la fuente de video: " + str(cam))
    while True:
        ret, img = cam.read()
        if not ret:
            print("Error al leer el fotograma de la cámara.")
            break

        img = cv2.resize(img, (640, 480))  # Reducir resolución si es necesario
        img_str = cv2.imencode('.jpg', img)[1].tobytes()

        start_time = time.time()
        client.publish(topic, img_str)

        end_time = time.time()
        latency = end_time - start_time
        print("Latency: {:.3f} seconds".format(latency))

# Función para detener el streaming
def stop_streaming(cam):
    if cam and cam.isOpened():
        cam.release()
    print("Streaming detenido.")

# Función principal para iniciar el streaming en un hilo
def start_streaming(topic, video_address=0, host="francasa.dyndns.org", port=1883):
    client, cam = initialize_stream(topic, video_address, host, port)
    if client and cam:
        streaming_thread = threading.Thread(target=stream_video, args=(client, cam, topic))
        streaming_thread.start()
        return streaming_thread, cam
    else:
        print("No se pudo iniciar el streaming.")
        return None, None

if __name__ == "__main__":
    topic = 'video/stream'
    thread, cam = start_streaming(topic=topic, video_address=0)

    try:
        input("Presiona Enter para detener el streaming...\n")
    finally:
        stop_streaming(cam)