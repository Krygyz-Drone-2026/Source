from ultralytics import YOLO
from ultralytics.engine.results import Results
import cv2
from djitellopy import Tello

# BGR color constants
BLUE   = (255, 0, 0)
RED    = (0, 0, 255)
GREEN  = (0, 255, 0)
YELLOW = (0, 255, 255)
WHITE  = (255, 255, 255)

# Load YOLOv8 model (use lowercase filename as stored in the repo)
model = YOLO('yolov8n.pt')

# Connect to Tello drone and start video stream
tello = Tello()
tello.connect()
tello.streamon()
print("Battery is " + str(tello.get_battery()))

# tello.takeoff()
# tello.move_up(40)

frame_read = tello.get_frame_read()

# EMA smoothing factor: lower = smoother but more lag, higher = more responsive
EMA_ALPHA = 0.3
smooth_box = None  # Stores the smoothed bounding box (x1, y1, x2, y2)

while True:
    # Get the latest frame from the drone camera
    tello_video_image = frame_read.frame
    frame_height, frame_width = tello_video_image.shape[:2]

    # Define left/right yaw threshold zones based on actual frame width
    left_threshold  = int(frame_width * 0.27)   # ~27% from left edge
    right_threshold = int(frame_width * 0.72)   # ~72% from left edge

    # Calculate and draw the drone's camera center point (blue circle)
    drone_cx = frame_width // 2
    drone_cy = frame_height // 2
    cv2.circle(tello_video_image, (drone_cx, drone_cy), 15, BLUE, 5)
    cv2.putText(tello_video_image, 'Drone', (drone_cx + 22, drone_cy + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLUE, 2)

    # Run YOLOv8 inference on the current frame
    results: list[Results] = model(tello_video_image)
    boxes = results[0].boxes  # Detected bounding boxes

    for box in boxes:
        # Use dict lookup instead of .pop() to avoid removing entries from the model
        class_name = model.names[int(box.cls.item())]

        # Only process detections of class 'person'
        if class_name != 'person':
            continue

        # Extract raw bounding box coordinates from YOLO
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = box.conf.item()

        # Apply EMA smoothing to bounding box coordinates
        # On first detection, initialize smooth_box with the raw values
        if smooth_box is None:
            smooth_box = (x1, y1, x2, y2)
        else:
            smooth_box = (
                EMA_ALPHA * x1 + (1 - EMA_ALPHA) * smooth_box[0],
                EMA_ALPHA * y1 + (1 - EMA_ALPHA) * smooth_box[1],
                EMA_ALPHA * x2 + (1 - EMA_ALPHA) * smooth_box[2],
                EMA_ALPHA * y2 + (1 - EMA_ALPHA) * smooth_box[3],
            )

        sx1, sy1, sx2, sy2 = [int(v) for v in smooth_box]

        # Draw smoothed bounding box and label
        cv2.rectangle(tello_video_image, (sx1, sy1), (sx2, sy2), GREEN, 3)
        cv2.putText(tello_video_image,
                    f'{class_name} {round(confidence, 2)}',
                    (sx1, sy1 - 6),
                    cv2.FONT_ITALIC, 1, GREEN, 2)

        # Calculate the center using smoothed coordinates
        centerX = int(sx1 + abs(sx1 - sx2) / 2)
        centerY = int(sy1 + abs(sy1 - sy2) / 2)
        print('center =', centerX, centerY)

        # Draw person center point (red circle) with label
        cv2.circle(tello_video_image, (centerX, centerY), 15, RED, 5)
        cv2.putText(tello_video_image, 'Person', (centerX + 22, centerY + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, RED, 2)

        # Draw a line from drone center to person center to show offset
        cv2.line(tello_video_image, (drone_cx, drone_cy), (centerX, centerY), YELLOW, 2)

        # Step 1: Align horizontally - rotate until person is in the center zone
        if centerX < left_threshold:
            print('yaw left')
            # tello.send_rc_control(0, 0, 0, -30)    # Rotate left (yaw CCW)
        elif centerX > right_threshold:
            print('yaw right')
            # tello.send_rc_control(0, 0, 0, 30)     # Rotate right (yaw CW)
        else:
            # Step 2: Person is centered - adjust distance based on bounding box area
            area = (sx2 - sx1) * (sy2 - sy1)
            if area < 15000:
                print('move forward - too far')
                # tello.send_rc_control(0, 20, 0, 0)     # Move forward (person too far)
            elif area > 30000:
                print('move backward - too close')
                # tello.send_rc_control(0, -20, 0, 0)    # Move backward (person too close)
            else:
                print('stop - good distance')
                # tello.send_rc_control(0, 0, 0, 0)      # Stop - at the right distance

        # Process only the first detected person per frame
        break
    else:
        # No person detected - stop the drone and reset smooth_box
        print('stop - no person')
        # tello.send_rc_control(0, 0, 0, 0)
        smooth_box = None

    # Display the frame with annotations
    cv2.imshow("YOLOv8 Person Follow", tello_video_image)

    # Press 'q' to stop and land
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()
