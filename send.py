#!/usr/bin/env python
import logging
import threading
import paho.mqtt.client as mqtt
import queue
import time

logging.basicConfig(level=logging.DEBUG)

broker_ip = "3.110.177.25"  # MQTT broker IP address
topic = "test"

class CommandPublisher:
    def __init__(self, topic, host="3.110.177.25", port=1883, start_publishing=True):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.connect(host, port, 60)
        self.topic = topic

        self.message_queue = queue.Queue(maxsize=3)  # Limit the size to prevent excessive memory usage

        self.publish_success_count = 0
        self.publish_total_count = 0

        self.publisher_thread = threading.Thread(target=self.publish_messages)
        
        if start_publishing:
            self.publisher_thread.start()

        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.debug("Connected successfully")
        else:
            logging.error(f"Connection failed with code {rc}")

    def on_publish(self, client, userdata, mid):
        self.publish_success_count += 1

    def start_publishing(self):
        if not self.publisher_thread.is_alive():
            self.publisher_thread = threading.Thread(target=self.publish_messages)
            self.publisher_thread.start()

    def publish_messages(self):
        while True:
            message = self.message_queue.get()
            if message is None:  # Exit signal
                break
            try:
                self.client.publish(self.topic, message, qos=1)
                self.publish_total_count += 1
            except Exception as e:
                logging.error(f"Failed to publish: {e}")
            
            # Adjust frame rate based on success rate
            if self.publish_total_count >= 10:  # Adjust every 10 frames
                success_rate = self.publish_success_count / self.publish_total_count
                if success_rate < 0.8:
                    logging.warning(f"Low success rate: {success_rate*100:.2f}%")
                elif success_rate > 0.9:
                    logging.info(f"High success rate: {success_rate*100:.2f}%")
                self.publish_success_count = 0
                self.publish_total_count = 0

            self.message_queue.task_done()

    def send_command(self, command):
        if command in ["0", "1"]:
            self.message_queue.put(command)
            logging.debug(f"Command queued: {command}")
        else:
            logging.debug("Invalid command. Please enter 0 or 1.")

if __name__ == "__main__":
    command_publisher = CommandPublisher(topic, broker_ip)
    try:
        while True:
            command = input("Enter 0 for open and 1 for close: ")
            command_publisher.send_command(command)
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        command_publisher.message_queue.put(None)  # Signal the publishing thread to exit
        command_publisher.publisher_thread.join()  # Wait for the thread to finish
        command_publisher.client.loop_stop()
        command_publisher.client.disconnect()
        logging.debug("Disconnected from broker")
