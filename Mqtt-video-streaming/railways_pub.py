import paho.mqtt.client as mqtt
import cv2
import threading
import queue
import time
import json
import random  # For generating random GPS coordinates

class StreamPublisher:
    def __init__(self, video_topic, gps_topic, video_address=0, start_stream=True, host="3.110.177.25", port=1883) -> None:
        self.client = mqtt.Client(protocol=mqtt.MQTTv311)
        self.client.max_inflight_messages_set(20)  # Set inflight messages
        self.client.max_message_size = 10485760  # Allow larger payload sizes (10 MB)  
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.connect(host, port, keepalive=60)
        self.client.loop_start()  
        
        self.video_topic = video_topic
        self.gps_topic = gps_topic
        self.video_source = video_address

        self.cam = cv2.VideoCapture(self.video_source)
        self.frame_rate = self.cam.get(cv2.CAP_PROP_FPS)
        self.frame_time = 1.0 / self.frame_rate

        self.frame_queue = queue.Queue(maxsize=2)

        self.capture_thread = threading.Thread(target=self.capture_frames)
        self.publish_thread = threading.Thread(target=self.publish_frames)
        self.gps_thread = threading.Thread(target=self.publish_gps)

        self.publish_success_count = 0
        self.publish_total_count = 0

        if start_stream:
            self.capture_thread.start()
            self.publish_thread.start()
            self.gps_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")

    def on_publish(self, client, userdata, mid):
        self.publish_success_count += 1

    def start_streaming(self):
        if not self.capture_thread.is_alive():
            self.capture_thread = threading.Thread(target=self.capture_frames)
            self.capture_thread.start()
        if not self.publish_thread.is_alive():
            self.publish_thread = threading.Thread(target=self.publish_frames)
            self.publish_thread.start()
        if not self.gps_thread.is_alive():
            self.gps_thread = threading.Thread(target=self.publish_gps)
            self.gps_thread.start()

    def capture_frames(self):
        print("Capturing from video source: {}".format(self.video_source))
        prev_capture_time = time.time()
        
        while True:
            current_time = time.time()
            elapsed_time = current_time - prev_capture_time

            if elapsed_time >= self.frame_time:
                ret, img = self.cam.read()
                if not ret:
                    print("Failed to read frame")
                    break  

                img_resized = cv2.resize(img, (640, 480))
                
                if not self.frame_queue.full():
                    self.frame_queue.put(img_resized)
                else:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(img_resized)
                    except queue.Empty:
                        pass
                
                prev_capture_time = current_time
        self.cam.release()

    def publish_frames(self):
        print("Publishing video to topic: {}".format(self.video_topic))
        while True:
            if not self.frame_queue.empty():
                img = self.frame_queue.get()
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                result, img_encoded = cv2.imencode('.jpg', img, encode_param)
                img_str = img_encoded.tobytes()
                try:
                    result = self.client.publish(self.video_topic, img_str)
                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        print(f"Publish failed with code: {result.rc}")
                    self.publish_total_count += 1
                except Exception as e:
                    print(f"Failed to publish: {e}")

                if self.publish_total_count >= 10:
                    success_rate = self.publish_success_count / self.publish_total_count
                    if success_rate < 0.8:
                        self.frame_rate = max(5, self.frame_rate - 1)
                    elif success_rate > 0.9:
                        self.frame_rate = min(30, self.frame_rate + 1)
                    self.frame_time = 1.0 / self.frame_rate
                    print(f"Adjusted frame rate to: {self.frame_rate}")
                    self.publish_success_count = 0
                    self.publish_total_count = 0
            time.sleep(0.1)

    def publish_gps(self):
        print(f"Publishing GPS and time to topic: {self.gps_topic}")
        while True:
            gps_data = {
                "latitude": random.uniform(-90, 90),
                "longitude": random.uniform(-180, 180),
                "timestamp": time.time()
            }
            gps_str = json.dumps(gps_data)
            try:
                self.client.publish(self.gps_topic, gps_str)
            except Exception as e:
                print(f"Failed to publish GPS data: {e}")
            time.sleep(1)

if __name__ == "__main__":
    webcam = StreamPublisher("video_topic", "gps_topic", video_address="new.avi")
