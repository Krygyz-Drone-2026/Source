import cv2
import time
from djitellopy import Tello

# Connect to the Tello drone
tello = Tello()
tello.connect(wait_for_state=False)

# Check and print battery level before flight
battery_level = tello.get_battery()
print(battery_level)

# Start video stream and get the frame reader
tello.streamon()
frame_read = tello.get_frame_read()
time.sleep(2)  # Wait for camera to initialize before capturing

# Take off, capture a single photo, then land
tello.takeoff()
cv2.imwrite("picture.png", frame_read.frame)  # Save current frame as PNG

# Print image size: (height, width, channels)
img = cv2.imread("picture.png")
print(img.shape)

tello.land()
tello.streamoff()
