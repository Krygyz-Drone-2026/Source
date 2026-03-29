# Lab-23.py
# Based on: https://github.com/DIT-AI-Drone-Course/SOURCE/blob/main/13_video_feed_flying_synchronous.py
# Synchronous flight pattern (move_up / move_down) with video feed
#
# Improvements over original:
#   - RGB → BGR color conversion for correct OpenCV display
#   - threading.Event for safe cross-thread signaling (replaces bare bool flag)
#   - Added frame delay (1/30 s) to reduce CPU usage
#   - Removed redundant destroyWindow call

import time
import cv2
from threading import Thread, Event
from djitellopy import Tello

speed = 25
MOVE_DISTANCE = 30   # cm
MOVE_INTERVAL = 3    # seconds

# threading.Event is safer than a bare bool for cross-thread signaling
stop_event = Event()


def flight_pattern():
    print("Takeoff!")
    tello.takeoff()

    if not tello.is_flying:
        # something happened... lets try one more time
        tello.takeoff()

    tello.move_up(20)
    time.sleep(1)

    up_flag = True
    t1 = time.time()

    while not stop_event.is_set():
        if time.time() - t1 > MOVE_INTERVAL:
            t1 = time.time()
            if up_flag:
                up_flag = False
                tello.move_up(MOVE_DISTANCE)
            else:
                up_flag = True
                tello.move_down(MOVE_DISTANCE)


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

# Signal flight_pattern thread to stop (will take effect after current move completes)
stop_event.set()
flight_pattern_thread.join(timeout=5)

tello.land()
time.sleep(1)

tello.streamoff()
cv2.destroyAllWindows()