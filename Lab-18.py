import cv2

# Open the default webcam (device index 0)
cap = cv2.VideoCapture(0)

# Define the video codec using DIVX (MPEG-4 compatible)
fourcc = cv2.VideoWriter_fourcc(*'DIVX')

# Read actual frame size from the webcam
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(frame_width, frame_height)  # 640, 480

# Create a VideoWriter object to save output as 'output.avi'
# Parameters: filename, codec, frame rate (25 fps), actual webcam resolution
out = cv2.VideoWriter('output.avi', fourcc, 25.0, (frame_width, frame_height))

# Main loop: runs as long as the camera is open
while cap.isOpened():
    ret, frame = cap.read()  # Read one frame from the webcam
    print('running')

    if ret:
        # Flip the frame vertically (0 = flip upside-down, 1 = flip left-right)
        # frame = cv2.flip(frame, 0)

        # Write the flipped frame to the output video file
        out.write(frame)

        # Display the flipped frame in a window named 'frame'
        cv2.imshow('frame', frame)

    # Wait 10ms for a key press; exit if 'q' is pressed
    # NOTE: the 'else: break' causes the loop to exit every iteration
    # regardless of key input — only one frame is captured in practice
    # wait 10 ms
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break
    else:
        break

# Release the webcam and video writer resources
cap.release()
out.release()

# Close all OpenCV display windows
cv2.destroyAllWindows()