# Lab-17: Webcam Video Capture with OpenCV
# Captures live video from the default webcam and displays it in a window.
# Press ESC to exit.

import cv2

# Open the default webcam (device index 0)
cap = cv2.VideoCapture(0)

# Print the resolution of the captured video
if cap.isOpened():
    print('width: {}, height : {}'.format(cap.get(3), cap.get(4)))

while True:
    ret, frame = cap.read()

    if ret:
        # Optional: convert to grayscale
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('video', gray)
        cv2.imshow('video', frame)

        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # 27 -> ESC
            break
    else:
        print('error')

# Release the webcam and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()
