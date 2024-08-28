import cv2
import threading
import numpy as np
import paho.mqtt.client as mqtt
import ffmpeg
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import logging

class StreamReceiver:

    def __init__(self, topic='', host="127.0.0.1", port=1883):
        self.topic = topic
        self.frame = None
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        
        # HLS parameters
        self.output_dir = './hls_output'
        self.hls_filename = 'stream.m3u8'
        self.hls_path = os.path.join(self.output_dir, self.hls_filename)

        # Clean up old HLS files
        self.clean_up_old_files()

        # FFMPEG process to convert frames to HLS
        try:
            self.ffmpeg_process = (
                ffmpeg
                .input('pipe:', format='rawvideo', pix_fmt='bgr24', s='640x480')
                .output(self.hls_path, format='hls', hls_time=5, hls_list_size=10, hls_flags='delete_segments+append_list', start_number=1)
                .global_args('-loglevel', 'info')
                .run_async(pipe_stdin=True)
            )
        except Exception as e:
            logging.error(f"Failed to start FFmpeg process: {e}")
            raise

        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.message_callback_add(self.topic, self.on_message)
        
        try:
            self.client.connect(host, port)
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")
            raise
        
        self.client.loop_start()

    def clean_up_old_files(self):
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                if filename.endswith(".ts") or filename == self.hls_filename:
                    file_path = os.path.join(self.output_dir, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logging.warning(f"Failed to delete file {file_path}: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info(f"Connected to MQTT broker. Subscribing to topic: {self.topic}")
            client.subscribe(self.topic)
        else:
            logging.error(f"Failed to connect to MQTT broker. Error code: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            nparr = np.frombuffer(msg.payload, np.uint8)
            self.frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if self.frame is not None:
                self.frame = cv2.resize(self.frame, (640, 480))
                self.ffmpeg_process.stdin.write(self.frame.tobytes())
            else:
                logging.warning("Received an empty or invalid frame")

        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def __del__(self):
        if hasattr(self, 'ffmpeg_process'):
            self.ffmpeg_process.stdin.close()
            self.ffmpeg_process.wait()
        if hasattr(self, 'client'):
            self.client.loop_stop()
            self.client.disconnect()
        cv2.destroyAllWindows()

def start_http_server(output_dir, port=5000):
    os.chdir(output_dir)
    
    handler = SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    logging.info(f"Serving HLS stream on http://localhost:{port}/stream.m3u8")
    httpd.serve_forever()

if __name__ == "__main__":
    receiver = StreamReceiver(topic="test")
    
    # Start the HTTP server on a separate thread
    http_server_thread = threading.Thread(target=start_http_server, args=(receiver.output_dir, 5000))
    http_server_thread.start()
