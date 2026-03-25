import cv2

img_file = "drone.jpeg"
img = cv2.imread(img_file)
title = 'IMG'         # Window title
x, y = 100, 100      # Initial window position

while True:
    cv2.imshow(title, img)  # type: ignore
    cv2.moveWindow(title, x, y)         # Move window to current position
    key = cv2.waitKey(0) & 0xFF         # Wait for key input, apply 8-bit mask
    print(key, chr(key))                # Print key code and character

    if key == ord('h'):                 # 'h' - move window left
        x -= 10
    elif key == ord('j'):               # 'j' - move window down
        y += 10
    elif key == ord('k'):               # 'k' - move window up
        y -= 10
    elif key == ord('l'):               # 'l' - move window right
        x += 10
    elif key == ord('q') or key == 27:  # 'q' or 'Esc' - quit
        break

cv2.destroyAllWindows()
