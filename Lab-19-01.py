import cv2
import time
from djitellopy import Tello

# ── Output image size settings ────────────────────────────
SAVE_WIDTH  = 480   # Desired output width  (original: 960)
SAVE_HEIGHT = 360   # Desired output height (original: 720)

# Connect to the Tello drone
tello = Tello()
tello.connect(wait_for_state=False)

# Check and print battery level before flight
battery_level = tello.get_battery()
print(f"Battery: {battery_level}%")

# Start video stream and get the frame reader
tello.streamon()
frame_read = tello.get_frame_read()
time.sleep(2)  # Wait for camera to initialize before capturing

# Take off and capture a single photo
# tello.takeoff()
frame = frame_read.frame

# Resize the captured frame to the desired dimensions
resized = cv2.resize(frame, (SAVE_WIDTH, SAVE_HEIGHT))
cv2.imwrite("picture.png", resized)

# Print original and saved image sizes
print(f"Original : {frame.shape[1]} x {frame.shape[0]}")
print(f"Saved    : {resized.shape[1]} x {resized.shape[0]}")

tello.land()
tello.streamoff()
