import cv2
from ultralytics import YOLO

# Load a pretrained YOLOv8n model (nano — fastest, least accurate)
# To use a custom model, replace with: YOLO('mask_detection.pt')
model = YOLO('yolov8n.pt')

# Open the default webcam (0) or replace with a video file path e.g. 'video.mp4'
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()  # Capture one frame
    if not ret:
        break

    # Run YOLOv8 inference on the current frame
    # conf=0.6: only show detections with confidence >= 60%
    results = model(frame, conf=0.6)

    # Overlay bounding boxes, labels, and confidence scores on the frame
    for r in results:
        frame = r.plot()

        # Print each detected object's class name and confidence to the console
        for box in r.boxes:
            cls_name = model.names[int(box.cls)]
            conf     = float(box.conf)
            print(f"{cls_name} {conf:.2f}")

    cv2.imshow('frame', frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release webcam and close all display windows
cap.release()
cv2.destroyAllWindows()
