from djitellopy import Tello
import cv2

tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")
tello.streamon()

# Get frame reader once (outside the loop)
frame_read = tello.get_frame_read()

# Display resolution
DISPLAY_W, DISPLAY_H = 480, 360

# Face area thresholds calibrated for 480x360 display
# A face at ~1.0m distance ≈ 5000–10000 px² in 480x360 frame
TARGET_MIN = 5000   # face too small → move forward
TARGET_MAX = 10000  # face too large → move back


def adjust_tello_position(offset_z):
    """
    Move forward/backward to maintain a target face size (distance control).
    :param offset_z: Area (w * h) of the detected face rectangle
    """
    if offset_z == 0:
        return
    if offset_z < TARGET_MIN:
        print(f'move_forward  (area={offset_z} < {TARGET_MIN})')
        tello.move_forward(20)
    elif offset_z > TARGET_MAX:
        print(f'move_back     (area={offset_z} > {TARGET_MAX})')
        tello.move_back(20)


# Load face detection model once (outside the loop for efficiency)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# tello.takeoff()
# tello.move_up(30)

while True:
    frame = frame_read.frame

    # Convert RGB (Tello) → BGR (OpenCV) and resize for display
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)

    # Display message if no face is detected
    if len(faces) == 0:
        cv2.putText(frame, '[No Face]', (DISPLAY_W - 220, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2, cv2.LINE_8)

    # Initial face area value
    z_area = 0

    for face in faces:
        (x, y, w, h) = face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)
        z_area = w * h
        cv2.putText(frame, f'[area={z_area}]', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2, cv2.LINE_8)

    adjust_tello_position(z_area)

    cv2.imshow('Tello detection...', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        tello.land()
        break
    elif key == ord('t'):
        tello.takeoff()
        tello.move_up(30)

# Stop stream and release resources
tello.streamoff()
tello.end()
cv2.destroyAllWindows()