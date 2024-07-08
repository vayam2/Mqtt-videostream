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
    client.loop_forever()  # Use loop_forever() to keep the script running

except Exception as e:
    logging.error(f"Error: {str(e)}")
