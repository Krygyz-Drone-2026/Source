import cv2
from djitellopy import Tello

# Connect to the Tello drone
tello = Tello()
tello.connect()

battery_level = tello.get_battery()
print(f"Battery: {battery_level}%")

# Start video stream and get the frame reader (once, outside the loop)
tello.streamon()
frame_read = tello.get_frame_read()

# Load Haar Cascade classifier once, outside the loop for performance
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascade_path)

while True:
    # Read the latest frame and resize (keep 4:3 aspect ratio)
    img = frame_read.frame
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)  # Tello returns RGB; convert to BGR for OpenCV
    img = cv2.resize(img, (480, 360))

    # Convert to grayscale for face detection
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces: scaleFactor=1.3, minNeighbors=5
    faces = faceCascade.detectMultiScale(imgGray, 1.3, 5)

    # Draw a red rectangle around each detected face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imshow('frame', img)

    # Press 'q' to quit
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()
