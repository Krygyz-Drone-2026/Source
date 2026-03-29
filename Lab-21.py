from djitellopy import Tello
import cv2

# Movement constants
STEP_CM = 30   # Distance per move command (cm)
STEP_DEG = 30  # Angle per rotation command (degrees)

# Connect to the Tello drone
tello = Tello()
tello.connect()

# Start video stream and get the frame reader object
tello.streamon()
frame_read = tello.get_frame_read()

# Automatically take off on start
tello.takeoff()

# Main control loop
while True:
    # Grab the latest frame from the drone camera
    img = frame_read.frame
    cv2.imshow("drone", img)

    # Wait 1ms for key input (returns -1 if no key pressed)
    key = cv2.waitKey(5) & 0xff

    if key == 27:  # ESC — exit loop and land
        break
    elif key == ord('w'):
        tello.move_forward(STEP_CM)             # Move forward
    elif key == ord('s'):
        tello.move_back(STEP_CM)                # Move backward
    elif key == ord('a'):
        tello.move_left(STEP_CM)                # Move left
    elif key == ord('d'):
        tello.move_right(STEP_CM)               # Move right
    elif key == ord('e'):
        tello.rotate_clockwise(STEP_DEG)        # Rotate clockwise
    elif key == ord('q'):
        tello.rotate_counter_clockwise(STEP_DEG)  # Rotate counter-clockwise
    elif key == ord('r'):
        tello.move_up(STEP_CM)                  # Move up
    elif key == ord('f'):
        tello.move_down(STEP_CM)                # Move down

# Land, stop stream, and close display window
tello.land()
tello.streamoff()
cv2.destroyAllWindows()