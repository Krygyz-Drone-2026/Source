import cv2

cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'DIVX')

# Use actual webcam resolution to avoid frame size mismatch
frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
out = cv2.VideoWriter('output.avi', fourcc, 25.0, (frame_width, frame_height))
print(frame_width, frame_height)

while cap.isOpened():
    ret, frame = cap.read()
    print('running')

    if ret:
        # image flip,  0:up-down, 1 : left-right
      frame = cv2.flip(frame, 0)
      out.write(frame)
      cv2.imshow('frame', frame)

    if cv2.waitKey(0) & 0xFF == ord('q'):
        break
    else:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
