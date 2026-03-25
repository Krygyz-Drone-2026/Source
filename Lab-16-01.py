import cv2
import yt_dlp

# YouTube video URL
# YOUTUBE_URL = 'https://www.youtube.com/watch?v=FVYxxHn8R-k'
YOUTUBE_URL = 'https://youtu.be/pn84aprnqkA?si=efpw8eTsnLikQwBQ'


# Extract the direct stream URL without downloading the file
print("Fetching stream URL...")
ydl_opts = {'format': 'best[ext=mp4]', 'quiet': True}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(YOUTUBE_URL, download=False)
    stream_url = info['url']
    print(f"Title: {info.get('title', 'Unknown')}")

# Open the YouTube stream directly with OpenCV (no download needed)
cap = cv2.VideoCapture(stream_url)

if not cap.isOpened():
    print("Failed to open stream. Check the URL or network connection.")
    exit()

print("Streaming... Press 'q' to quit.")

# Loop as long as the stream is open
while cap.isOpened():
    ret, frame = cap.read()  # Read the next frame; ret=True if successful

    if ret:
        # Display the color frame
        cv2.imshow('YouTube Stream', frame)

        # Wait 10ms per frame; exit loop if 'q' is pressed
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    else:
        # Frame read failed — end of stream or network error
        print('Stream ended or read error.')
        break

# Release the capture resource and close all display windows
cap.release()
cv2.destroyAllWindows()
