import cv2
from djitellopy import Tello
from cvzone.FaceMeshModule import FaceMeshDetector

# Connect to the Tello drone
me = Tello()
me.connect(wait_for_state=False)

print(f"Battery: {me.get_battery()}%")

# Start video stream and get frame reader once (outside the loop)
me.streamon()
frame_read = me.get_frame_read()

# Initialize FaceMesh detector (limit to 1 face for performance)
detector = FaceMeshDetector(maxFaces=1)

while True:
    # Read frame and convert RGB (Tello) → BGR (OpenCV)
    img = frame_read.frame
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Detect face mesh — returns image with mesh drawn and list of 468 landmarks per face
    img, faces = detector.findFaceMesh(img)

    # Print landmark coordinates of the first detected face
    if faces:
        print(faces[0])

    cv2.imshow("Face Mesh", img)

    # Press 'q' to quit
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Stop stream and close all windows
me.streamoff()
cv2.destroyAllWindows()
