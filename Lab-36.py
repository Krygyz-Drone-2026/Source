from djitellopy import Tello
import cv2

tello = Tello()
tello.connect()
print(f"Battery: {tello.get_battery()}%")
tello.streamon()

# Get frame reader once (outside the loop)
frame_read = tello.get_frame_read()


def adjust_tello_position(offset_z):
    """
    Adjusts the position of the Tello drone based on the detected face area.
    Moves forward when face is too small (far away), backward when too large (too close).
    Uses blocking move commands — only triggers when outside the target range.
    :param offset_z: Area (w * h) of the face detection rectangle in 480x360 frame
    """
    if offset_z == 0:
        return
    if offset_z < TARGET_MIN:
        tello.move_forward(20)
        print(f'move_forward  (area={offset_z} < {TARGET_MIN})')
    elif offset_z > TARGET_MAX:
        tello.move_back(20)
        print(f'move_back     (area={offset_z} > {TARGET_MAX})')


# Load face detection model once (outside the loop for efficiency)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Use display resolution (480x360) for center calculation
DISPLAY_W, DISPLAY_H = 480, 360
center_x = DISPLAY_W // 2
center_y = DISPLAY_H // 2

# Face area thresholds calibrated for 480x360 display
# A face at ~1.0m distance ≈ 5000–10000 px² in 480x360 frame
TARGET_MIN = 5000   # face too small → move forward
TARGET_MAX = 10000  # face too large → move back

# tello.takeoff()
# tello.move_up(30)

while True:
    frame = frame_read.frame

    # Convert RGB (Tello) → BGR (OpenCV) and resize for display
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    frame = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))

    # Draw the center point of the frame
    cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0), 8)

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

        # Calculate face center correctly (x-axis uses w, y-axis uses h)
        face_center_x = x + w // 2
        face_center_y = y + h // 2
        z_area = w * h

        cv2.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255), 8)
        cv2.putText(frame, f'[{z_area}]', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2, cv2.LINE_8)

        # Adjust drone forward/backward based on face area
        adjust_tello_position(z_area)

    # Show frame outside the for loop so it always updates
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
