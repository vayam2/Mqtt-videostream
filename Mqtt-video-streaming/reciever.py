#!/usr/bin/env python

import cv2
import threading
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import signal
import sys
import datetime
import time

class StreamReceiver:
    def __init__(self, eo_video_topic='', ir_video_topic='', gps_topic='', host="65.0.71.42", port=1883):
        self.eo_video_topic = eo_video_topic
        self.ir_video_topic = ir_video_topic
        self.gps_topic = gps_topic
        self.eo_frame = None  # Stores latest EO video frame
        self.ir_frame = None  # Stores latest IR video frame
        self.gps_data = None  # Stores latest GPS data

        # Create separate video files for EO and IR streams
        self.start_time = datetime.datetime.now()
        self.eo_video_file = self.start_time.strftime("EO_%Y-%m-%d_%H-%M-%S.avi")
        self.ir_video_file = self.start_time.strftime("IR_%Y-%m-%d_%H-%M-%S.avi")
        self.gps_file_path = self.start_time.strftime("GPS_%Y-%m-%d_%H-%M-%S.txt")
        
        # Create or clear the GPS data file
        with open(self.gps_file_path, 'w') as file:
            file.write("Timestamp, Latitude, Longitude\n")

        self.eo_out = None  # VideoWriter object for EO stream
        self.ir_out = None  # VideoWriter object for IR stream
        self.frame_width = 640  # Default frame width
        self.frame_height = 480  # Default frame height
        self.crop_height = 50  # Number of rows to crop from the top
        
        # MQTT setup
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.message_callback_add(self.eo_video_topic, self.on_eo_video_message)
        self.client.message_callback_add(self.ir_video_topic, self.on_ir_video_message)
        self.client.message_callback_add(self.gps_topic, self.on_gps_message)

        try:
            self.client.connect(host, port)
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            sys.exit(1)

        self.running = True
        t = threading.Thread(target=self.subscribe)
        t.start()

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

    def subscribe(self):
        self.client.loop_forever()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(self.eo_video_topic)
            client.subscribe(self.ir_video_topic)
            client.subscribe(self.gps_topic)
            print(f"Subscribed to topics: {self.eo_video_topic}, {self.ir_video_topic}, and {self.gps_topic}")
        else:
            print(f"Failed to connect, return code: {rc}")

    def on_eo_video_message(self, client, userdata, msg):
        self.process_video_message(msg, stream_name="EO", out_file=self.eo_video_file, out_writer_attr="eo_out")

    def on_ir_video_message(self, client, userdata, msg):
        self.process_video_message(msg, stream_name="IR", out_file=self.ir_video_file, out_writer_attr="ir_out")

    def process_video_message(self, msg, stream_name, out_file, out_writer_attr):
        nparr = np.frombuffer(msg.payload, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is not None:
            # Crop the frame by removing the top rows
            frame = frame[self.crop_height:, :]

            # Display the video stream
            cv2.imshow(f'{stream_name} Video Stream', frame)

            # Initialize the VideoWriter if not already done
            out_writer = getattr(self, out_writer_attr)
            if out_writer is None:
                frame_height, frame_width, _ = frame.shape
                out_writer = cv2.VideoWriter(
                    out_file,
                    cv2.VideoWriter_fourcc(*'XVID'),
                    15,  # Adjust FPS as necessary
                    (frame_width, frame_height)
                )
                setattr(self, out_writer_attr, out_writer)

            # Write the frame to the video file
            out_writer.write(frame)

            # Timing adjustment for consistent frame rate
            desired_fps = 20
            desired_time_per_frame = 1.0 / desired_fps
            elapsed_time = time.time() % desired_time_per_frame
            if elapsed_time < desired_time_per_frame:
                time.sleep(desired_time_per_frame - elapsed_time)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.shutdown()

    def on_gps_message(self, client, userdata, msg):
        self.gps_data = json.loads(msg.payload)
        print(f"Received GPS data: {self.gps_data}")

        # Convert the timestamp to a human-readable datetime format
        timestamp = self.gps_data.get("timestamp", "N/A")
        try:
            dt_object = datetime.datetime.fromtimestamp(int(timestamp))
            formatted_timestamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            formatted_timestamp = "Invalid Timestamp"

        latitude = self.gps_data.get("latitude", "N/A")
        longitude = self.gps_data.get("longitude", "N/A")

        # Print the converted timestamp along with GPS data
        print(f"Timestamp: {formatted_timestamp}, Latitude: {latitude}, Longitude: {longitude}")

        # Save the formatted timestamp and GPS data to the new GPS file
        with open(self.gps_file_path, 'a') as file:
            file.write(f"{formatted_timestamp}, {latitude}, {longitude}\n")

    def shutdown(self, signum=None, frame=None):
        print("Shutting down...")
        self.running = False
        self.client.disconnect()

        # Release video writers
        if self.eo_out is not None:
            self.eo_out.release()
        if self.ir_out is not None:
            self.ir_out.release()

        cv2.destroyAllWindows()
        sys.exit(0)

if __name__ == "__main__":
    receiver = StreamReceiver(
        eo_video_topic="eo_video_topic",
        ir_video_topic="ir_video_topic",
        gps_topic="gps_topic"
    )
