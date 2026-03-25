import cv2
from djitellopy import Tello
from ultralytics import YOLO

# Initialize Tello drone
tello = Tello()
tello.connect(wait_for_state=False)

# Start video stream and get the frame reader once (outside the loop)
tello.streamon()
frame_read = tello.get_frame_read()

# Load a pretrained YOLOv8n model (nano — fastest)
# To use a custom model, replace with: YOLO('mask_detection.pt')
model = YOLO('yolov8n.pt')

try:
    while True:
        # Read frame and convert RGB (Tello) → BGR (OpenCV)
        frame = frame_read.frame
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(frame, (480, 360))  # Resize for faster inference

        # Run YOLOv8 inference; only show detections with confidence >= 60%
        results = model(frame, conf=0.6)

        # Overlay bounding boxes, labels, and confidence scores on the frame
        for r in results:
            frame = r.plot()

        cv2.imshow('Tello YOLOv8', frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # Ensure stream is stopped and resources are released even on error
    tello.streamoff()
    tello.end()
    cv2.destroyAllWindows()
