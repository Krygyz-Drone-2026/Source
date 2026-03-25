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

# Face area thresholds calibrated for 480x360 display
# A face at ~1.0m distance ≈ 5000–10000 px² in 480x360 frame
TARGET_MIN = 5000   # face too small → move forward
TARGET_MAX = 10000  # face too large → move back


def adjust_tello_position(offset_x, offset_y, offset_z):
    """
    Adjusts drone position on all three axes based on face offset and area.
    :param offset_x: face_center_x - frame_center_x (negative=left, positive=right)
    :param offset_y: face_center_y - frame_center_y - 30 (negative=above, positive=below)
    :param offset_z: Area (w * h) of the detected face rectangle
    """
    # X-axis (yaw): rotate to center face horizontally
    if not -90 <= offset_x <= 90:
        if offset_x < 0:
            print('rotate_counter_clockwise')
            # tello.rotate_counter_clockwise(10)
        elif offset_x > 0:
            print('rotate_clockwise')
            # tello.rotate_clockwise(10)

    # Y-axis (altitude): move up/down to center face vertically
    if not -70 <= offset_y <= 70:
        if offset_y < 0:
            print('move_up')
            # tello.move_up(20)
        elif offset_y > 0:
            print('move_down')
            # tello.move_down(20)

    # Z-axis (distance): move forward/backward based on face area
    if offset_z == 0:
        return
    if offset_z < TARGET_MIN:
        print(f'move_forward  (area={offset_z} < {TARGET_MIN})')
        # tello.move_forward(20)
    elif offset_z > TARGET_MAX:
        print(f'move_back     (area={offset_z} > {TARGET_MAX})')
        # tello.move_back(20)


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

    # Default values when no face detected (offsets = 0 → no command)
    face_center_x = center_x
    face_center_y = center_y
    z_area = 0

    for face in faces:
        (x, y, w, h) = face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)

        face_center_x = x + w // 2
        face_center_y = y + h // 2
        z_area = w * h

        cv2.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255), 6)

        # Draw line from face center to frame center
        cv2.line(frame, (face_center_x, face_center_y), (center_x, center_y), (255, 0, 0), 2)

    # Calculate offsets from frame center
    offset_x = face_center_x - center_x
    # Subtract 30 to keep face slightly above center (captures more of the subject)
    offset_y = face_center_y - center_y - 30

    cv2.putText(frame, f'[x={offset_x}, y={offset_y}, area={z_area}]', (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2, cv2.LINE_8)
    adjust_tello_position(offset_x, offset_y, z_area)

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