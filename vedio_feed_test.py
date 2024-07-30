import dronekit as dk 
import time
import datetime 
import cv2
import numpy
import os

#os.system("mavproxy.py --out 127.0.0.1:6969 --baudrate 57600 > /tmp/test.log")
print("sleep cm")
time.sleep(2)

path ='/media/nuc/data'
 
# Check whether the specified
# path exists or not
isExist = os.path.exists(path)
if isExist == True:
    ls = os.listdir('/media/nuc')
    print(len(ls))
    if(len(ls) > 1):
        os.system('umount /dev/sda1')
        os.system('sudo rm -rf /media/nuc/data')
        os.system('sudo reboot now')
    vehicle = dk.connect('127.0.0.1:6969', baud = 57600) # connect to the vehicle, use mavproxy
    print(vehicle.location.global_relative_frame.lat, vehicle.location.global_relative_frame.lat)
    print("connected?")

    # while(True):
    #     lat_string = f'Vehicle latitude: {vehicle.location.global_relative_frame.lat} '
    #     # lon_string = f'Vehicle longitude: {vehicle.location.global_relative_frame.lon} '
    #     print(lat_string)
    #     x = dk.Locations(vehicle)
    #     print(x)
    #     time.sleep(1)




    lat = 1
    lon = 1


    default_lat_string = "Vehicle Latitude: ???"
    default_lon_string = "Vehicle Longitude: ???"

    cap = cv2.VideoCapture(1)
    cap.set(3,1280)
    cap.set(4,720)
    date = str(datetime.datetime.now())
    date = date[5:10] + ' ' + date[11:13] + '-' + date[14:16]
    if(not os.path.exists(path)):
        sys.exit(0)
    final_string = f'/media/nuc/data/video/{date}.avi'
    print(final_string)
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(final_string, fourcc, 20.0, (1280,620))
    font = cv2.FONT_HERSHEY_SIMPLEX

    delta1 = 0
    delta2 = 1

    while(True):
        
        if(not os.path.exists(path)):
            sys.exit(0)
        ret, frame = cap.read()
        if(frame is None):
            continue
        frame = frame[100:720, 0:1280]
        latitude = vehicle.location.global_relative_frame.lat
        longitude = vehicle.location.global_relative_frame.lon
        if(latitude is not None):
            lat_string = f'Vehicle latitude: {latitude} '
        else:
            lat_string = default_lat_string
        
        if(longitude is not None):
            lon_string = f'Vehicle longitude: {longitude} '
        else:
            lon_string = default_lon_string
        dt = str(datetime.datetime.now())
        cap_fps = cap.get(cv2.CAP_PROP_FPS)
        delta2 = time.time()
        fps = 1/(delta2 - delta1)
        print(fps)
        delta1 = delta2
        data_string = f'{lat_string}  {lon_string}  time: {dt} '
        processed_frame = cv2.putText(frame, data_string, 
                            (10, 600), 
                            font, 0.5, 
                            (1, 1, 255),  
                            1, cv2.LINE_AA)
        
        out.write(processed_frame)
        folder_path = 'data/video'
        filename = f"{date}.txt"
        # Define the full path to the file
        print("df")
        file_path = os.path.join(folder_path, filename)
    
        # Open the file for writing
        with open(file_path, 'w') as file:
        # Write a header line (optional)
            file.write('Latitude,Longitude,Timestamp\n')
        if not isinstance(timestamp, str):
            timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        file.write(f'{latitude},{longitude},{dt}\n')
        #cv2.imshow('frame', processed_frame)
        
        #c = cv2.waitKey(1)
        #if c & 0xFF == ord('q'):
            #break

    cap.release()
    out.release()
    cv2.destroyAllWindows() 
else:
    print("ssd not connected")
