from ultralytics import YOLO
from ultralytics.engine.results import Results
import cv2, math, time
from djitellopy import Tello

# Create a Tello drone instance and establish a Wi-Fi connection (192.168.10.1)
tello = Tello()
tello.connect()

# Start the video stream from the drone's front camera
tello.streamon()
# Get the frame reader object; frame_read.frame gives the latest BGR image
frame_read = tello.get_frame_read()

# --- Model Loading ---
# Load YOLOv8 nano pretrained weights (COCO 80-class general detector)
model = YOLO('yolov8n.pt')
# Alternatively, load a custom-trained model (e.g., mask detection)
# model = YOLO('Mask_best_200_epoch.pt')

# --- Main Inference Loop ---
while True:
    # Allow OpenCV to process GUI events (keeps the window responsive)
    cv2.waitKey(5)

    # Grab the latest frame from the drone video stream
    tello_video_image = frame_read.frame

    # Get the latest frame, convert RGB (Tello) → BGR (OpenCV)
    input_image= cv2.cvtColor(tello_video_image, cv2.COLOR_RGB2BGR)

    image= cv2.resize(input_image, (480, 360))

    # Run YOLOv8 inference on the current frame
    # Returns a list of Results objects (one per image, here always use index 0)
    results: list[Results] = model(image)

    # Render bounding boxes, class labels, and confidence scores onto the frame
    annotated_frame = results[0].plot()

    # Display the annotated frame in a named OpenCV window
    cv2.imshow("YOLOv8 Inference", annotated_frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Stop the video stream before disconnecting
tello.streamoff()
# Close all OpenCV display windows
cv2.destroyAllWindows()