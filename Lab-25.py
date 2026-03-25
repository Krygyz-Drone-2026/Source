import cv2
import urllib.request
import numpy as np

src = cv2.imread('lena.png')

# Load Haar Cascade classifier for front face detection
# cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
cascade_path = 'haarcascade_frontalface_default.xml'
classifier = cv2.CascadeClassifier(cascade_path)

# Detect faces in the input image
faces = classifier.detectMultiScale(src)

# Draw a rectangle around each detected face
# cv2.rectangle expects (x, y) top-left and (x+w, y+h) bottom-right corners
for (x, y, w, h) in faces:
    cv2.rectangle(src, (x, y), (x + w, y + h), (255, 0, 255), 2)

cv2.imshow('src', src)
cv2.waitKey(0)
cv2.destroyAllWindows()
