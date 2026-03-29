from cvzone.FaceMeshModule import FaceMeshDetector
import cv2

# Open the default webcam (index 0)
cap = cv2.VideoCapture(0)

# Initialize FaceMesh detector; limit detection to 1 face
detector = FaceMeshDetector(maxFaces=1)

while True:
    # Capture a frame from the webcam
    success, img = cap.read()

    # Detect face mesh landmarks; returns annotated image and list of faces
    # Each face is a list of 468 (x, y) landmark points
    img, faces = detector.findFaceMesh(img)

    if faces:
        # Print the 468 landmark coordinates of the first detected face
        print(faces[0])

    # Display the annotated frame
    cv2.imshow("Image", img)

    # Press 'q' to quit the loop
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

# Release webcam and close all windows
cap.release()
cv2.destroyAllWindows()