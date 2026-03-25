import cv2
from djitellopy import Tello
from cvzone.FaceDetectionModule import FaceDetector

# Connect to the Tello drone
me = Tello()
me.connect(wait_for_state=False)

# get_battery() needs state packet; skip if not yet available
try:
    print(f"Battery: {me.get_battery()}%")
except Exception:
    print("Battery level unavailable")

# Start video stream and get frame reader once (outside the loop)
me.streamon()
frame_read = me.get_frame_read()

# Initialize cvzone FaceDetector
detector = FaceDetector()

while True:
    # Read frame and convert RGB (Tello) → BGR (OpenCV)
    img = frame_read.frame
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Detect faces and draw bounding boxes on the frame
    # bboxs: list of detected face info (id, bbox, score, center)
    img, bboxs = detector.findFaces(img, draw=True)

    cv2.imshow("Image", img)

    # Press 'q' to quit
    if cv2.waitKey(5) & 0xFF == ord('q'):
        break

# Stop stream and close all windows
me.streamoff()
cv2.destroyAllWindows()
