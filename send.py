# # echo-server.py

# import socket

# HOST = "3.110.177.25"  # Standard loopback interface address (localhost)
# PORT = 1883  # Port to listen on (non-privileged ports are > 1023)

# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.bind((HOST, PORT))
#     s.listen()
#     conn, addr = s.accept()
#     with conn:
#         print(f"Connected by {addr}")
#         while True:
#             # data = conn.recv(1024)
#             data = input("enter data")

#             if not data:
#                 break
#             conn.sendall(data.encode())





import logging
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.DEBUG)

broker_ip = "3.110.177.25"  # MQTT broker IP address
topic = "test"


def on_connect(client, userdata, flags, rc):
    logging.debug(f"Connected with result code {rc}")
    client.subscribe(topic)

def on_message(client, userdata, msg):
    logging.debug(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(broker_ip, 1883, 6900)
    client.loop_start()
    while 1:
        message = input("enter 0 for open and 1 for close")
        # Publish a message
        client.publish(topic, message)
        print("sended")

    # Keep the script running to receive messages
    while True:
        pass

except Exception as e:
    logging.error(f"Error: {str(e)}")