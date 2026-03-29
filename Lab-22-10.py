# Lab-22-10.py
# Based on: https://github.com/DIT-AI-Drone-Course/SOURCE/blob/main/12_video_feed_flying.py
# Improvements:
#   - RGB → BGR color conversion for correct OpenCV display
#   - Stop RC control (0,0,0,0) before landing to prevent command conflicts
#   - Added frame delay (1/30 s) to reduce CPU usage
#   - Removed redundant destroyWindow call

import time
import cv2
from threading import Thread
from djitellopy import Tello

speed = 20

def flight_pattern():
    print("Takeoff!")
    tello.takeoff()

    if not tello.is_flying:
        # something happened... lets try one more time
        tello.takeoff()

    time.sleep(1)
    tello.move_up(20)
    time.sleep(1)

    up_flag = True
    t1 = time.time()

    while True:
        if time.time() - t1 > 3:
            t1 = time.time()
            if up_flag:
                up_flag = False
                tello.send_rc_control(0, 0, speed, 0)
            else:
                up_flag = True
                tello.send_rc_control(0, 0, -speed, 0)

tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")

time.sleep(2)

tello.streamon()
frame_read = tello.get_frame_read()

# daemon=True: main thread 종료 시 자동으로 스레드도 종료됨
flight_pattern_thread = Thread(target=flight_pattern, daemon=True)
flight_pattern_thread.start()

time.sleep(2)
print("Press 'q' to quit")

while True:
    frame = frame_read.frame
    if frame is None:
        continue

    # Tello outputs RGB; convert to BGR for OpenCV
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("Tello Video", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(1 / 30)

# Stop RC control before landing to prevent command conflicts
tello.send_rc_control(0, 0, 0, 0)
time.sleep(0.5)

tello.land()
time.sleep(1)

tello.streamoff()
cv2.destroyAllWindows()