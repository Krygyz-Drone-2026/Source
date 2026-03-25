from djitellopy import Tello
import cv2
import time


def clamp(value: int, limit: int) -> int:
    """Limit speed commands to the Tello allowed range [-limit, limit]."""
    return max(-limit, min(limit, value))


tello = Tello()
tello.connect()
print(f"battery: {tello.get_battery()}%")
tello.streamon()
airborne = False


def adjust_tello_position(offset_z, face_center, frame_center, frame_area):
    """
    Adjust position based on face size (distance) and center offsets.
    Runs continuously with send_rc_control: forward/back = distance,
    yaw = left/right centering, up/down = vertical centering.
    :param offset_z: Area (width * height) of the detected face rectangle
    :param face_center: (x, y) center of detected face
    :param frame_center: (x, y) center of the video frame
    :param frame_area: width * height of the video frame
    """
    if offset_z == 0:
        tello.send_rc_control(0, 0, 0, 0)
        return

    # Distance control using normalized face area for resolution independence
    area_ratio = offset_z / frame_area
    target_min, target_max = 0.02, 0.045  # ~2%–4.5% of frame area
    fb_speed = 0
    if area_ratio < target_min:
        fb_speed = 20  # move forward
    elif area_ratio > target_max:
        fb_speed = -20  # move backward

    # Centering control (yaw + altitude) with small deadband to reduce jitter
    cx, cy = face_center
    fx, fy = frame_center
    error_x = fx - cx  # + => face is left of center
    error_y = fy - cy  # + => face is above center
    deadband_px = 15
    yaw_speed = 0 if abs(error_x) < deadband_px else -clamp(int(error_x * 0.1), 40)
    ud_speed = 0 if abs(error_y) < deadband_px else clamp(int(error_y * 0.1), 30)

    tello.send_rc_control(0, fb_speed, ud_speed, yaw_speed)


# Load face detection model once (outside the loop for efficiency)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
frame_read = tello.get_frame_read()

# Use display resolution (480x360) for all area calculations
width, height = 480, 360
frame_area = width * height   # 172800
print('height:', height, '  width:', width)

# Frame center based on display size (480x360)
center_x = 240
center_y = 180


try:
    while True:
        # Abort gracefully if the video thread has stopped (e.g., link lost)
        if frame_read.stopped:
            print("Video stream stopped; landing for safety.")
            break

        frame = frame_read.frame
        if frame is None or frame.size == 0:
            # No fresh frame; avoid flying on stale data
            print("No frame received; stopping RC.")
            tello.send_rc_control(0, 0, 0, 0)
            time.sleep(0.1)
            continue

        # Draw the center point of the frame
        cv2.circle(frame, (center_x, center_y), 10, (0, 255, 0), 8)

        # Convert RGB (Tello) → BGR (OpenCV) and resize for display
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (480, 360))

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, minNeighbors=5)

        # Display message if no face is detected
        if len(faces) == 0:
            print('face not found')
            cv2.putText(frame, '[No Face]', (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_8)

        # Initial face area value
        z_area = 0
        face_center = None

        for face in faces:
            (x, y, w, h) = face

            # Draw rectangle around the detected face
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)

            # Calculate the center of the detected face
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            z_area = w * h
            face_center = (face_center_x, face_center_y)

            # Draw the face center point
            cv2.circle(frame, (face_center_x, face_center_y), 10, (0, 0, 255), 8)

            # Display the face area size on the frame
            cv2.putText(frame, f'[{z_area}]', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_8)

        # Control drone only when exactly one face is detected (avoid conflicting commands)
        if airborne and len(faces) == 1:
            adjust_tello_position(z_area, face_center, (center_x, center_y), frame_area)
        else:
            # Stop if no or multiple faces (prevents lingering motion on stale command)
            tello.send_rc_control(0, 0, 0, 0)

        # Show the frame (outside the for loop so it always updates)
        cv2.imshow('Tello detection...', frame)

        # Handle key input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):       # 'q' = land (if airborne) and quit
            if airborne:
                tello.land()
                airborne = False
            break
        elif key == ord('t') and not airborne:  # 't' = single takeoff + lift buffer
            tello.takeoff()
            tello.move_up(30)
            airborne = True
finally:
    # Ensure motors stop and resources are released even on error/Exit
    tello.send_rc_control(0, 0, 0, 0)
    if airborne:
        try:
            tello.land()
        except Exception:
            pass
    try:
        tello.streamoff()
    except Exception:
        pass
    tello.end()
    cv2.destroyAllWindows()
