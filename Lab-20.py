from djitellopy import Tello
import cv2
import time

# Connect to the Tello drone
tello = Tello()
tello.connect(wait_for_state=False)

# Check and print battery level before streaming
battery_level = tello.get_battery()
print(f"Battery: {battery_level}%")

# Start video stream and wait for camera to initialize
print("Turn Video Stream On")
tello.streamon()
frame_read = tello.get_frame_read()  # Create frame reader once, outside the loop
time.sleep(2)

# Main loop: continuously display the resized drone video feed
while True:
    # Read the latest frame from the Tello video stream
    tello_video_image = frame_read.frame

    # Resize the frame for display (original: 960x720)
    image = cv2.resize(tello_video_image, (480, 360))

    # Display the resized frame in an OpenCV window
    if image is not None:
        cv2.imshow("TelloVideo", image)

    # Press 'q' to quit the video stream
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the video stream and close all display windows
tello.streamoff()
cv2.destroyAllWindows()
