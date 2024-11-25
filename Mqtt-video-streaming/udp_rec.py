import cv2
import socket
import json
import numpy as np

class StreamReceiver:
    def __init__(self, video_port=5000, gps_port=5001, server_ip="3.110.177.25"):
        # Create UDP sockets for receiving video and GPS data
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.gps_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind sockets to respective ports
        self.video_socket.bind((server_ip, video_port))  # Bind to server IP
        self.gps_socket.bind((server_ip, gps_port))  # Bind to server IP

        print(f"Listening for video on {server_ip}:{video_port} and GPS on {server_ip}:{gps_port}")

    def receive_video(self):
        print("Receiving video frames")
        while True:
            data, addr = self.video_socket.recvfrom(65536)  # 64KB buffer
            img_array = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is not None:
                cv2.imshow("Received Video", img)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                    break
        cv2.destroyAllWindows()

    def receive_gps(self):
        print("Receiving GPS data")
        while True:
            data, addr = self.gps_socket.recvfrom(1024)  # Buffer size of 1KB
            gps_data = json.loads(data.decode())
            print(f"Received GPS data: {gps_data}")

    def start(self):
        # Start both video and GPS receivers
        threading.Thread(target=self.receive_video).start()
        threading.Thread(target=self.receive_gps).start()

if __name__ == "__main__":
    receiver = StreamReceiver(video_port=5000, gps_port=5001, server_ip="3.110.177.25")
    receiver.start()
