import cv2

# Open the video file for reading
cap = cv2.VideoCapture('video.mp4')

# Loop as long as the video capture is open
while(cap.isOpened()):
    ret, frame = cap.read()  # Read the next frame; ret=True if successful

    if ret:
        # Convert the frame from BGR color to grayscale
        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Display the grayscale frame in a window named 'frame'
        # cv2.imshow('frame', gray)
        
        # color frame
        cv2.imshow('frame', frame)
        
        # Wait 1ms for key input; exit loop if 'q' is pressed
        # if cv2.waitKey(10) & 0xFF == ord('q'):
        #     break
        
        if cv2.waitKey(0) & 0xFF == ord('q'):
            break
    else:
        # Frame read failed — end of file or corrupted frame
        print('error')
        break  # Exit loop to avoid infinite error output

# Release the video capture resource and close all display windows
cap.release()
cv2.destroyAllWindows()
