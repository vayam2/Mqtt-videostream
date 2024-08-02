import dronekit as dk
import time
import datetime
import cv2
import os,sys

def check_and_reboot_if_needed(path):
    if os.path.exists(path):
        if len(os.listdir('/media/rpi')) > 1:
            os.system('umount /dev/sda1')
            os.system('sudo rm -rf /media/rpi/data')
            os.system('sudo reboot now')

def connect_to_vehicle(connection_string, baudrate):
    vehicle = dk.connect(connection_string, baud=baudrate, wait_ready=True)
    if not vehicle:
        print("Failed to connect to vehicle.")
        sys.exit(1)
    return vehicle

def setup_video_writer(path, date):
    final_string = f'{path}/video/{date}.avi'
    print(final_string)
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(final_string, fourcc, 20.0, (1280, 620))
    return out

def main():
    print("sleep cm")
    time.sleep(1)

    path = '/home/rpi/Downloads'
    
    # Check and reboot if needed
    check_and_reboot_if_needed(path)

    # Connect to the vehicle
    vehicle = connect_to_vehicle('127.0.0.1:6969', 57600)
    print(f"Vehicle connected at location: {vehicle.location.global_relative_frame.lat}, {vehicle.location.global_relative_frame.lon}")

    default_lat_string = "Vehicle Latitude: ???"
    default_lon_string = "Vehicle Longitude: ???"

    cap = cv2.VideoCapture('rtsp://192.168.2.119:8554/eo')
    cap.set(3, 1280)
    cap.set(4, 720)
    date = str(datetime.datetime.now())
    date = date[5:10] + ' ' + date[11:13] + '-' + date[14:16]

    if not os.path.exists(path):
        print("Path does not exist.")
        sys.exit(0)

    out = setup_video_writer(path, date)
    font = cv2.FONT_HERSHEY_SIMPLEX

    delta1 = 0

    folder_path = f'{path}/video/'
    filename = f"{date}.txt"
    file_path = os.path.join(folder_path, filename)
    
    # Open the file for writing and write the header
    with open(file_path, 'w') as file:
        file.write('Latitude,Longitude,Timestamp\n')

    while True:
        if not os.path.exists(path):
            sys.exit(0)
        
        ret, frame = cap.read()
        if frame is None:
            continue

        frame = frame[100:720, 0:1280]
        latitude = vehicle.location.global_relative_frame.lat
        longitude = vehicle.location.global_relative_frame.lon
        lat_string = f'Vehicle latitude: {latitude}' if latitude else default_lat_string
        lon_string = f'Vehicle longitude: {longitude}' if longitude else default_lon_string
        dt = str(datetime.datetime.now())
        cap_fps = cap.get(cv2.CAP_PROP_FPS)
        delta2 = time.time()
        fps = 1 / (delta2 - delta1)
        print(fps)
        delta1 = delta2

        data_string = f'{lat_string}  {lon_string}  time: {dt} '
        processed_frame = cv2.putText(frame, data_string, (10, 600), font, 0.5, (1, 1, 255), 1, cv2.LINE_AA)
        out.write(processed_frame)
        
        with open(file_path, 'a') as file:
            timestamp = dt if isinstance(dt, str) else dt.strftime('%Y-%m-%d %H:%M:%S')
            file.write(f'{latitude},{longitude},{timestamp}\n')

    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
