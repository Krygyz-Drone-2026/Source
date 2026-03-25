import cv2
from djitellopy import Tello

# Connect to the Tello drone
tello = Tello()
tello.connect()
battery_level = tello.get_battery()
print(f"Battery: {battery_level}%")

# Start video stream and create frame reader once (outside the loop)
tello.streamon()
frame_read = tello.get_frame_read()

# Load Haar Cascade classifier once for performance
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascade_path)

while True:
    # Read frame and convert RGB (Tello) → BGR (OpenCV)
    img = frame_read.frame
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, (480, 360))  # 4:3 aspect ratio

    # Detect faces on grayscale image
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(imgGray, 1.2, 8)

    for (x, y, w, h) in faces:
        # Draw red bounding box around detected face
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Calculate face center point and bounding box area
        cx = x + w // 2   # Center x
        cy = y + h // 2   # Center y
        area = w * h       # Face area in pixels (used for distance estimation)

        # Draw green dot at face center
        cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)
        print(f"area = {area}  center = ({cx}, {cy})")

    cv2.imshow('frame', img)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

tello.streamoff()
cv2.destroyAllWindows()
