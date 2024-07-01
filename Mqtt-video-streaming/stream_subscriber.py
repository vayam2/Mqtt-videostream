#!/usr/bin/env python

import cv2
import threading
import paho.mqtt.client as mqtt
import subprocess

class Stream_publisher:
    
    def __init__(self, topic, video_address=0, start_stream=True, host="3.110.177.25", port=1883) -> None:
        
        self.client = mqtt.Client()  # MQTT client instance
        self.client.connect(host, port)  # Connect to MQTT Broker
        self.topic = topic  # MQTT topic to publish stream
        self.video_source = video_address  # Video source address

        self.cam = cv2.VideoCapture(self.video_source)  # OpenCV VideoCapture object

        self.streaming_thread = threading.Thread(target=self.stream)  # Thread for streaming
        if start_stream:
            self.streaming_thread.start()  # Start streaming thread
    
    def start_streaming(self):
        """
        Start the streaming thread manually.
        """
        self.streaming_thread.start()

    def stream(self):
        """
        Stream video frames via MQTT after compressing with FFmpeg.
        """
        print("Streaming from video source: {}".format(self.video_source))

        # FFmpeg command to compress frames using hardware-accelerated H.264 encoding
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', '640x480',
            '-r', '30',
            '-i', 'pipe:0',
            '-vcodec', 'h264_v4l2m2m',
            '-pix_fmt', 'yuv420p',
            '-f', 'rawvideo',
            'pipe:1'
        ]

        # Start FFmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Print FFmpeg stderr in a separate thread for debugging
        def print_ffmpeg_stderr(stderr):
            for line in iter(stderr.readline, b''):
                print(f"FFmpeg stderr: {line.decode().strip()}")

        stderr_thread = threading.Thread(target=print_ffmpeg_stderr, args=(process.stderr,))
        stderr_thread.start()

        # Loop to read frames from webcam and stream via MQTT
        while True:
            ret, img = self.cam.read()  # Read frame from webcam
            if not ret:
                print("Failed to read from video source")
                break

            img = cv2.resize(img, (640, 480))  # Resize frame to 640x480

            try:
                process.stdin.write(img.tobytes())  # Write frame to FFmpeg stdin
            except BrokenPipeError as e:
                print(f"BrokenPipeError: {e}")
                break

            try:
                out_frame = process.stdout.read(640 * 480 * 3 // 2)  # Read compressed frame from FFmpeg stdout
                if len(out_frame) == 0:
                    print("Failed to read output frame from FFmpeg")
                    break
                self.client.publish(self.topic, out_frame)  # Publish frame via MQTT
            except Exception as e:
                print(f"Exception: {e}")
                break

        # Close FFmpeg process and threads
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()
        process.wait()

if __name__ == "__main__":
    # Example usage: streaming from webcam (0) to MQTT topic "test"
    webcam = Stream_publisher("test", video_address=0)
    # For streaming from a video file, use the file path instead:
    # webcam = Stream_publisher("test", video_address="path_to_video_file.mkv")
