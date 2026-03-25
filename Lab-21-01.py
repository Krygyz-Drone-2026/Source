from djitellopy import Tello
import cv2

# Velocity constant for all movement commands (-100 ~ 100)
SPEED = 30

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
    key = cv2.waitKey(1) & 0xff

    if key == 27:  # ESC — exit loop and land
        break
    elif key == ord('w'):
        tello.send_rc_control(0, SPEED, 0, 0)    # Move forward
    elif key == ord('s'):
        tello.send_rc_control(0, -SPEED, 0, 0)   # Move backward
    elif key == ord('a'):
        tello.send_rc_control(-SPEED, 0, 0, 0)   # Move left
    elif key == ord('d'):
        tello.send_rc_control(SPEED, 0, 0, 0)    # Move right
    elif key == ord('r'):
        tello.send_rc_control(0, 0, SPEED, 0)    # Move up
    elif key == ord('f'):
        tello.send_rc_control(0, 0, -SPEED, 0)   # Move down
    elif key == ord('e'):
        tello.send_rc_control(0, 0, 0, SPEED)    # Rotate clockwise
    elif key == ord('q'):
        tello.send_rc_control(0, 0, 0, -SPEED)   # Rotate counter-clockwise
    else:
        tello.send_rc_control(0, 0, 0, 0)        # No key — stop all movement

# Land, stop stream, and close display window
tello.land()
tello.streamoff()
cv2.destroyAllWindows()