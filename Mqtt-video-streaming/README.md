# MQTT Video Stream Publisher

This project demonstrates how to use a Raspberry Pi with OpenCV to capture video frames from a webcam or video file and publish them to an MQTT broker. The setup uses `paho-mqtt` for MQTT communication and `opencv-python` for video processing.

## Prerequisites

Ensure you have the following installed and configured:

1. **Hardware:**
   - Raspberry Pi (any model with GPIO support)
   - Webcam (if streaming from a webcam)

2. **Software:**
   - Python 3
   - OpenCV
   - paho-mqtt

## Installation

1. **Update and Upgrade your Raspberry Pi:**

    ```bash
    sudo apt-get update
    sudo apt-get upgrade
    ```

2. **Install Python and pip:**

    ```bash
    sudo apt-get install python3 python3-pip
    ```

3. **Install OpenCV:**

    ```bash
    pip3 install opencv-python opencv-python-headless
    ```

4. **Install paho-mqtt:**

    ```bash
    pip3 install paho-mqtt
    ```
5. Install Mqtt Broker

    ```bash
    sudo apt-get install mosquitto
    sudo apt-get install mosquitto-clients
    ```
   
## Running the Code

1. **Download or Clone the Repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Run the publisher script:**

    ```bash
    python3 Stream_publisher.py
    ```
    The script will start capturing video from the webcam (default) and publishing frames to the MQTT broker.

3. **Run the reciver script:**

    ```bash
    python3 Stream_reciever.py
    ```
   The script will start displaying video frames recieved from the MQTT broker.

## Code Explanation

### Stream_publisher Class

#### Initialization

The `Stream_publisher` class initializes the MQTT client, connects to the broker, and starts the video capture and publishing threads.

- `topic`: MQTT topic to publish frames to.
- `video_address`: Source of the video (default is `0` for webcam).
- `start_stream`: Boolean to start streaming immediately (default is `True`).
- `host`: MQTT broker host (default is `"127.0.0.1"`).
- `port`: MQTT broker port (default is `1883`).

#### Methods

- `on_connect`: Callback for successful MQTT connection.
- `on_publish`: Callback for successful message publishing.
- `start_streaming`: Starts the video capture and publishing threads if they are not already running.
- `capture_frames`: Captures frames from the video source and puts them in a queue.
- `publish_frames`: Publishes frames from the queue to the MQTT broker and adjusts the frame rate based on the success rate.

### Main Script

The main script creates an instance of `Stream_publisher` and starts streaming from the webcam to the MQTT topic `"test"`.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenCV for providing the tools for image processing.
- Eclipse Paho for the MQTT library.
