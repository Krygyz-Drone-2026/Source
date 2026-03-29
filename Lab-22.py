import time
import cv2
from threading import Thread
from djitellopy import Tello

tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")

tello.streamon()
frame_read = tello.get_frame_read()

keepRecording = True

def videoRecorder():
    # we need to run the recorder in a separate thread, otherwise blocking commands
    # would prevent frames from being displayed
    while keepRecording:
        frame = frame_read.frame
        if frame is None:
            continue

        # Tello outputs RGB; convert to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (360 * 2, 240 * 2))

        cv2.imshow('Tello Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        time.sleep(1 / 30)

    cv2.destroyAllWindows()

recorder = Thread(target=videoRecorder)
recorder.start()

tello.takeoff()
tello.move_up(30)
tello.rotate_counter_clockwise(360)
tello.land()

keepRecording = False
recorder.join()
tello.streamoff()