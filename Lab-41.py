# =============================================================
# Lab-41: Tello Face Tracking with PID Control
#
# How it works:
#   1. Get live video stream from the Tello drone
#   2. Detect a face in each frame using FaceDetector
#   3. Calculate the error between the face position and
#      the center of the frame (X, Y axes)
#   4. Calculate the error between the face bounding box area
#      and a target area (Z axis = forward/backward distance)
#   5. Feed each error into a PID controller to get correction values
#   6. Send correction values as RC control commands to the drone
# =============================================================

from djitellopy import Tello
import cv2
import cvzone
from cvzone.FaceDetectionModule import FaceDetector
from cvzone.PIDModule import PID
from cvzone.PlotModule import LivePlot

# ── Face Detector ─────────────────────────────────────────
# minDetectionCon: minimum confidence score to accept a detection (0~1)
detector = FaceDetector(minDetectionCon=0.5)

# ── Frame Size ────────────────────────────────────────────
hi, wi = 480, 640   # height, width of the video frame in pixels

# ── PID Controllers ───────────────────────────────────────
# PID([P, I, D], setpoint)
#   P (Proportional) : reacts to current error
#   I (Integral)     : reacts to accumulated error over time
#   D (Derivative)   : reacts to rate of change of error
#
# setpoint = target value the PID tries to reach
#   xPID : target = horizontal center of frame (wi // 2)
#   yPID : target = vertical center of frame   (hi // 2)
#   zPID : target = face bounding box area of 12000 px² (ideal distance)

xPID = PID([0.22,  0, 0.1  ], wi // 2)                    # controls yaw (rotate left/right)
yPID = PID([0.27,  0, 0.1  ], hi // 2, axis=1)            # controls throttle (move up/down)
zPID = PID([0.005, 0, 0.003], 12000, limit=[-30, 30])     # controls forward/backward speed
# limit was [-20, 15] → widened to [-30, 30] so output is not always clamped flat

# ── Live Plot Windows ─────────────────────────────────────
# Visualize PID output values in real time for each axis
myPlotX = LivePlot(yLimit=[-100, 100], char='X')   # yaw correction
myPlotY = LivePlot(yLimit=[-100, 100], char='Y')   # throttle correction
myPlotZ = LivePlot(yLimit=[-35, 35], char='Z')     # forward/back correction — match zPID limit range

# ── Drone Setup ───────────────────────────────────────────
me = Tello()
me.connect()
print(f"Battery: {me.get_battery()}%")

me.streamoff()   # stop any existing stream before starting fresh
me.streamon()    # start receiving video frames from the drone

# me.takeoff()   # uncomment when ready to fly
# me.move_up(80) # gain altitude after takeoff for better face detection

# ── Main Loop ─────────────────────────────────────────────
while True:
    # Step 1: Grab the latest frame from the drone camera
    img = me.get_frame_read().frame
    img = cv2.resize(img, (wi, hi))   # resize to fixed frame size

    # Step 2: Detect faces — returns annotated image and list of bounding boxes
    img, bboxs = detector.findFaces(img, draw=True)

    # Default control values (no movement when no face detected)
    xVal = yVal = zVal = 0

    if bboxs:
        # Step 3: Extract face info from the first detected face
        cx, cy = bboxs[0]['center']      # center point of face (pixels)
        x, y, w, h = bboxs[0]['bbox']   # bounding box (x, y, width, height)
        area = w * h                     # area used to estimate distance

        # Step 4: Compute PID correction values
        # PID output = how much to move to reduce the error to zero
        xVal = int(xPID.update(cx))    # error = cx - center_x  → yaw command
        yVal = int(yPID.update(cy))    # error = cy - center_y  → throttle command
        zVal = int(round(zPID.update(area)))  # round before int to avoid small values truncating to 0
        # error = area - 12000   → forward/back command

        print(f"xVal={xVal}  yVal={yVal}  zVal={zVal}")

        # Step 5: Update live plots with the correction values
        imgPlotX = myPlotX.update(xVal)
        imgPlotY = myPlotY.update(yVal)
        imgPlotZ = myPlotZ.update(zVal)

        # Step 6: Draw PID error lines/arrows on the frame
        img = xPID.draw(img, [cx, cy])
        img = yPID.draw(img, [cx, cy])
        img = zPID.draw(img, [cx, cy])

        # Show bounding box area value on the frame (used for Z distance estimation)
        cv2.putText(img, f"Area: {area}", (20, 50),
                    cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        # Stack: drone frame + 3 PID plots in a 2-column grid
        imgStacked = cvzone.stackImages([img, imgPlotX, imgPlotY, imgPlotZ], 2, 0.75)

    else:
        # No face detected — show drone frame only
        imgStacked = cvzone.stackImages([img], 1, 0.75)

    # ── Drone RC Control ──────────────────────────────────
    # send_rc_control(left/right, forward/back, up/down, yaw)
    #   xVal  → yaw      : rotate drone to center face horizontally
    #  -yVal  → up/down  : negate because screen Y is flipped vs drone Y
    #  -zVal  → forward  : negate because larger area = too close = move back
    # me.send_rc_control(0, -zVal, -yVal, xVal)   # uncomment to activate

    # ── Display ───────────────────────────────────────────
    cv2.imshow("Face Tracking", imgStacked)

    # Press 'q' to quit
    if cv2.waitKey(5) & 0xFF == ord('q'):
        # me.land()   # uncomment when flying
        break

cv2.destroyAllWindows()
