import cv2

image_file = "drone.jpeg"

color_image = cv2.imread(image_file, cv2.IMREAD_COLOR)  # Read as a 3-channel color image (BGR)
gray_image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)  # Read as a single-channel grayscale image
original_image = cv2.imread(image_file, cv2.IMREAD_UNCHANGED)  # Keep the original number of channels

if color_image is None or gray_image is None or original_image is None:
    raise FileNotFoundError(f"이미지 파일을 읽을 수 없습니다: {image_file}")

cv2.imshow("Color Image", color_image)
cv2.imshow("Gray Image", gray_image)
cv2.imshow("Unchanged Image", original_image)

cv2.waitKey(0)
cv2.destroyAllWindows()
