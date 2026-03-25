import cv2

# Open the default webcam (device index 0)
cap = cv2.VideoCapture(0)

# Load Haar Cascade classifier once, outside the loop for performance
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascade_path)

while True:
    ret, img = cap.read()  # Read frame from webcam
    if not ret:
        print("Failed to read frame")
        break

    img = cv2.resize(img, (480, 360))  # Resize to 4:3 aspect ratio

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

cap.release()
cv2.destroyAllWindows()
