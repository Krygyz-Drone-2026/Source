import cv2
from djitellopy import Tello

tello = Tello()
tello.connect()
battery_level = tello.get_battery()
print(battery_level)
tello.streamon()
frame_read = tello.get_frame_read()  

# Load face detection model once before the loop (not inside the loop)
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

while True:
    # Get the latest frame, convert RGB (Tello) → BGR (OpenCV), then resize
    img = frame_read.frame
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.resize(img, (480, 360))

    # Convert to grayscale for face detection
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(imgGray, 1.3, 5)

    # Show face detection status on screen
    status = "Face Found" if len(faces) > 0 else "Face Not Found"
    color  = (0, 255, 0)  if len(faces) > 0 else (0, 0, 255)
    cv2.putText(img, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Center point derived from actual frame size (avoids hardcoding)
    tcx = img.shape[1] // 2
    tcy = img.shape[0] // 2
    cv2.circle(img, (tcx, tcy), 10, (255, 0, 0), cv2.FILLED)

    # Draw a rectangle around each detected face
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # Calculate the center point and area of the detected face
        cx   = x + w // 2
        cy   = y + h // 2
        area = w * h
        cv2.circle(img, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

        # Display face info on screen instead of printing to console
        cv2.putText(img, f"area={area}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Draw a line from the face center to the frame center
        cv2.line(img, (cx, cy), (tcx, tcy), (255, 0, 0), 2)

    cv2.imshow('AI Drone ', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
        break

tello.streamoff()
cv2.destroyAllWindows()
