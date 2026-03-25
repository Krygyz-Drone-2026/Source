from djitellopy import Tello
import cv2

tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")
tello.streamon()

# Get frame reader once (outside the loop)
frame_read = tello.get_frame_read()

# Display resolution and frame center
DISPLAY_W, DISPLAY_H = 480, 360
center_x = DISPLAY_W // 2
center_y = DISPLAY_H // 2

# Deadband: ignore small offsets within ±90px to reduce jitter
DEADBAND = 90


def adjust_tello_position(offset_x):
    """
    Adjusts yaw (rotation) based on horizontal offset of the face from frame center.
    :param offset_x: face_center_x - frame_center_x (negative=left, positive=right)
    """
    if not -DEADBAND <= offset_x <= DEADBAND:
        if offset_x < 0:
            # Face is left of center → rotate counter-clockwise
            tello.rotate_counter_clockwise(10)
            print(f'rotate_counter_clockwise  (offset_x={offset_x})')
        else:
            # Face is right of center → rotate clockwise
            tello.rotate_clockwise(10)
            print(f'rotate_clockwise          (offset_x={offset_x})')


# Load face detection model once (outside the loop for efficiency)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# tello.takeoff()
# tello.move_up(30)

while True:
    frame = frame_read.frame

    # Convert RGB (Tello) → BGR (OpenCV) and resize for display
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

    # Draw the center point of the frame
    cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0), 6)

    # Convert to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)

    # Display message if no face is detected
    if len(faces) == 0:
        cv2.putText(frame, '[No Face]', (DISPLAY_W - 220, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2, cv2.LINE_8)

    # Default: face center = frame center → offset = 0 → no rotation
    face_center_x = center_x

    for face in faces:
        (x, y, w, h) = face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)

        # Calculate face center correctly (x-axis uses w, y-axis uses h)
        face_center_x = x + w // 2
        face_center_y = y + h // 2

        cv2.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255), 6)

    # Calculate horizontal offset and adjust yaw
    offset_x = face_center_x - center_x
    cv2.putText(frame, f'[offset_x={offset_x}]', (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2, cv2.LINE_8)
    adjust_tello_position(offset_x)

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