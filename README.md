# Solar Boat
_Solar Boat_ is a **Wireless Solar Boat** developed as part of the course "[Redes Inalámbricas y Móviles](https://secretaria.uvigo.gal/docnet-nuevo/guia_docent/?centre=305&ensenyament=V05G301V01&assignatura=V05G301V01402&any_academic=2024_25)" in the Telecommunications Engineering Degree at the Universidad de Vigo (2024 - 2025).

## About The Project
This project implements a distributed monitoring and communication system for a solar-powered marine vessel, enabling real-time data collection, automated alerts, and remote control through a ground-based server. The system integrates multiple wireless communication technologies to evaluate their performance under different operational conditions.

The project features:
- Raspberry Pi-based onboard system for data collection.
- Sensor integration for temperature, acceleration, gyroscope, compass, and heading data.
- MQTT and Zenoh protocol for efficient and reliable message-based communication.
- Automated alerts for overheating prevention and manual emergency stops.
- Flask-based web interface for real-time monitoring and control.
- SQLite database for persistent storage of sensor data.
- Dockerized MQTT broker with dynamic DNS configuration for remote access.

## How To Run
### Hardware
This project was developed using the following hardware:
- [Raspberry Pi 4 Model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/)
- [Arduino Grove Base Shield](https://store.arduino.cc/en-es/products/grove-base-shield-v2-0-for-arduino)
- [Ultrasonic Distance Sensor HC SR-04](https://www.sparkfun.com/ultrasonic-distance-sensor-hc-sr04.html)
- [Grove - IMU 9DOF](https://www.seeedstudio.com/Grove-IMU-9DOF-v2-0.html)
- [Logitech C270 HD Webcam](https://www.logitech.com/es-es/products/webcams/c270-hd-webcam.960-001063.html)
- [Huawei E3372](https://consumer.huawei.com/gh/support/routers/e3372/)
- [Sixfab LTE-M Cellular IoT Kit](https://sixfab.com/product/raspberry-pi-cellular-iot-kit-lte-m/)
- [USRP B200mini](https://www.ettus.com/all-products/usrp-b200mini/)
- [HTCC-AB02A](https://heltec.org/project/htcc-ab02a/)
- [SX-NEWAH-EVK-US](https://www.silextechnology.com/connectivity-solutions/embedded-wireless/sx-newah-evaluation)

### Arduino
Flash the Arduino Shield with the [`sensor.ino`](src/arduino/sensor.ino) code.

### MQTT Broker
Follow the steps in [`MQTT Broker.pdf`](docs/Configs/[MQTT%20Broker]%20Configs.pdf) to set up the MQTT Broker.

The broker can be hosted on the same machine as the server or any other device, as long as it is accessible from the Internet.

### Boat
In the device acting as the server, copy the [`boat/`](src/boat/) directory.
Modify the `DOMAIN` and `PORT` variables (lines 21 and 22) in [`boat.py`](src/boat/boat.py) according to your MQTT broker.

Make sure the Arduino Shield is connected to port `/dev/ttyUSB0`. Otherwise, modify line 53 as well.

*Some Python modules may need to be installed.*

### Server
In the device acting as the server, copy the [`server/`](src/server/) directory.
Modify the `DOMAIN` and `PORT` variables (lines 16 and 17) in [`server.py`](src/server/server.py) according to your MQTT broker.

*Some Python modules may need to be installed.*

### LTE
To run the system using the LTE technology, set up your USB Modem to get Internet connectivity on the boat device. 

Then start up the MQTT Broker, and run files `boat.py` and `server.py` in the boat and server, respectively, with:
#### Boat
```bash
python3 boat/boat.py
```
#### Server
```bash
python3 server/server.py
```

Access `http://localhost:8080` from the server device to view the interface.

### NB-IoT
To run the system using the NB-IoT technology, follow the instructions available in [`NB-IoT.pdf`](docs/Configs/NB-IoT.pdf) to get Internet connectivity on the boat device.

Then start up the MQTT Broker, and run files `boat.py` and `server.py` in the boat and server, respectively, with:
#### Boat
```bash
python3 boat/boat.py
```
#### Server
```bash
python3 server/server.py
```

Access `http://localhost:8080` from the server device to view the interface.

### Private LTE
To run the system using the Private LTE technology, follow the instructions available in [`LTE Priv.pdf`](docs/Configs/LTE%20Priv.pdf) to get Internet connectivity on the boat device.

Then start up the MQTT Broker, and run files `boat.py` and `server.py` in the boat and server, respectively, with:
#### Boat
```bash
python3 boat/boat.py
```
#### Server
```bash
python3 server/server.py
```

Access `http://localhost:8080` from the server device to view the interface.

### LoRaWAN
To run the system using the LoRaWAN technology, follow the instructions available in [`LoRaWAN.pdf`](docs/Configs/LoRaWAN.pdf).

*The files mentioned in the document are available in the [`lora/`](src/lora) directory.*

### BLE
To run the system using the BLE technology, follow the instructions available in [`BLE.pdf`](docs/Configs/BLE.pdf).

In the device acting as the server, copy the [sub.py](src/ble/sub.py) file.

In the device acting as the boat, copy the [pub.py](src/ble/pub.py) file.
Modify the `SERVER_MAC` variable (line 7) according to the server MAC address.

*Some Python modules may need to be installed.*

Then run files `pub.py` and `sub.py` in the boat and server, respectively, with:
#### Boat
```bash
python3 pub.py
```
#### Server
```bash
python3 sub.py
```

Access `http://localhost:8080` from the server device to view the data  received.

### WiFi HaLow
To run the system using the WiFi HaLow technology, follow the instructions available in [`WiFi Halow.pdf`](docs/Configs/WiFi%20Halow.pdf).

*The files mentioned in the document are available in the [`halow/`](src/halow) directory.*

## About The Code
Refer to [`Specifications.pdf`](docs/Specifications.pdf), [`Tecnologías.pdf`](docs/Comparisons/Tecnologías.pdf), and [`Presentación`](docs/Presentación.pdf) for a high-level overview of the project.