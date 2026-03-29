import cv2
import djitellopy
from djitellopy import Tello
from ultralytics import YOLO
from ultralytics.engine.results import Results

# BGR color constants (OpenCV uses BGR, not RGB)
SKYBLUE = (255, 255, 0)   # Cyan in BGR
YELLOW  = (0, 255, 255)   # Yellow in BGR
BLUE    = (255, 0, 0)
RED     = (0, 0, 255)
GREEN   = (0, 255, 0)
WHITE   = (255, 255, 255)

# label {'No Mask', 'Mask Wearing'}
model = YOLO('Mask_best_200_epoch.pt')

# init tello
tello: Tello = djitellopy.Tello()
tello.connect()
tello.streamon()

# tello.set_speed(50)
print("Battery is " + str(tello.get_battery()))

# tello.takeoff()
# tello.move_up(40)
# tello.send_rc_control(0, 0, 40, 0)

frame_read = tello.get_frame_read()

# Frame width: 960px  → left threshold: 320, right threshold: 640 (equal thirds)
FRAME_LEFT_THRESHOLD  = 320
FRAME_RIGHT_THRESHOLD = 640

while True:
    cv2.waitKey(1)

    tello_video_image = frame_read.frame

    results: list[Results] = model(tello_video_image)

    boxes = results[0].boxes  # Boxes object for bbox outputs

    for box in boxes:
        # Use indexing instead of pop() — pop() permanently removes the key from the dict
        class_name = model.names[int(box.cls.item())]
        print(class_name)

        # Extract bounding box coordinates once (shared by all classes)
        x1, y1, x2, y2 = (
            box.xyxy[0][0].item(),
            box.xyxy[0][1].item(),
            box.xyxy[0][2].item(),
            box.xyxy[0][3].item(),
        )
        confidence = box.conf.item()

        # Draw label and bounding box with color based on class
        if class_name == 'Mask Wearing':
            color = GREEN
        elif class_name == 'No Mask':
            color = RED
        else:
            color = WHITE

        label = f"{class_name} {round(confidence, 2)}"
        cv2.putText(tello_video_image, label, (int(x1), int(y1) - 6),
                    cv2.FONT_ITALIC, 1, color, 2)
        cv2.rectangle(tello_video_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)

        # Compute bounding box center
        centerX = int(x1 + (abs(x1 - x2) / 2))
        centerY = int(y1 + (abs(y1 - y2) / 2))
        print('center =', centerX, centerY)

        cv2.circle(tello_video_image, (centerX, centerY), 15, RED, 5)

        # Drone yaw control based on horizontal position of detected object
        if centerX < FRAME_LEFT_THRESHOLD:
            print('yaw -30 (object is left)')
            # tello.send_rc_control(0, 0, 0, -30)
        elif centerX > FRAME_RIGHT_THRESHOLD:
            print('yaw +30 (object is right)')
            # tello.send_rc_control(0, 0, 0, 30)
        else:
            print('forward (object is centered)')
            # tello.send_rc_control(0, 40, 0, 0)

    # Display the annotated frame
    cv2.imshow("YOLOv8 Inference", tello_video_image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()