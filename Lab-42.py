# =============================================================
# Lab-42: Tello Gesture Control
# Source: https://github.com/kinivi/tello-gesture-control
#
# REQUIRED model files (place next to this script):
#   model/keypoint_classifier/keypoint_classifier.tflite
#   model/keypoint_classifier/keypoint_classifier_label.csv
#   model/point_history_classifier/point_history_classifier.tflite
#   model/point_history_classifier/point_history_classifier_label.csv
#
# Install dependencies:
#   pip install djitellopy opencv-python mediapipe tensorflow
#
# Controls:
#   SPACE  : takeoff / land
#   k      : switch to keyboard mode (WASD / Q,E,R,F)
#   g      : switch to gesture mode
#   n      : data logging mode (record new gestures)
#   ESC    : quit
# =============================================================

import os
import csv
import copy
import threading
import itertools
from collections import Counter, deque

import cv2 as cv
import numpy as np
import mediapipe as mp
from ai_edge_litert.interpreter import Interpreter as TFLiteInterpreter
from djitellopy import Tello

# ── Script directory (for loading model files) ───────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Configuration (replace configargparse with simple defaults) ─
DEVICE                 = 0
WIDTH, HEIGHT          = 960, 720
IS_KEYBOARD            = True      # True = keyboard mode on startup
USE_STATIC_IMAGE_MODE  = False
MIN_DETECTION_CONF     = 0.7
MIN_TRACKING_CONF      = 0.7
BUFFER_LEN             = 10

# =============================================================
# Utility: FPS Calculator
# =============================================================
class CvFpsCalc:
    def __init__(self, buffer_len=1):
        self._start_tick = cv.getTickCount()
        self._freq = 1000.0 / cv.getTickFrequency()
        self._difftimes = deque(maxlen=buffer_len)

    def get(self):
        current_tick = cv.getTickCount()
        different_time = (current_tick - self._start_tick) * self._freq
        self._start_tick = current_tick
        self._difftimes.append(different_time)
        fps = 1000.0 / (sum(self._difftimes) / len(self._difftimes))
        return round(fps, 2)


# =============================================================
# Model: KeyPoint Classifier (hand sign classification)
# Loads a TFLite model trained on 21 hand landmarks (42 values)
# =============================================================
class KeyPointClassifier:
    def __init__(self, num_threads=1):
        model_path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier',
                                  'keypoint_classifier.tflite')
        self.interpreter = TFLiteInterpreter(model_path=model_path,
                                               num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def __call__(self, landmark_list):
        idx = self.input_details[0]['index']
        self.interpreter.set_tensor(idx, np.array([landmark_list], dtype=np.float32))
        self.interpreter.invoke()
        result = self.interpreter.get_tensor(self.output_details[0]['index'])
        return int(np.argmax(np.squeeze(result)))


# =============================================================
# Model: Point History Classifier (finger movement pattern)
# Classifies the trajectory history of the index fingertip
# =============================================================
class PointHistoryClassifier:
    def __init__(self, score_th=0.5, invalid_value=0, num_threads=1):
        model_path = os.path.join(BASE_DIR, 'model', 'point_history_classifier',
                                  'point_history_classifier.tflite')
        self.interpreter = TFLiteInterpreter(model_path=model_path,
                                               num_threads=num_threads)
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.score_th      = score_th
        self.invalid_value = invalid_value

    def __call__(self, point_history):
        idx = self.input_details[0]['index']
        self.interpreter.set_tensor(idx, np.array([point_history], dtype=np.float32))
        self.interpreter.invoke()
        result = self.interpreter.get_tensor(self.output_details[0]['index'])
        result_index = int(np.argmax(np.squeeze(result)))
        # If confidence is below threshold, return invalid
        if np.squeeze(result)[result_index] < self.score_th:
            result_index = self.invalid_value
        return result_index


# =============================================================
# Gesture Recognition
# Uses MediaPipe Hands to detect hand landmarks, then classifies
# the hand sign (keypoint) and fingertip movement (point history)
# =============================================================
class GestureRecognition:
    def __init__(self, use_static_image_mode=False,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7,
                 history_length=16):
        self.history_length = history_length

        # MediaPipe Hands setup
        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=use_static_image_mode,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        # Load TFLite classifiers
        self.keypoint_classifier       = KeyPointClassifier()
        self.point_history_classifier  = PointHistoryClassifier()

        # Load label CSV files
        kp_label_path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier',
                                     'keypoint_classifier_label.csv')
        ph_label_path = os.path.join(BASE_DIR, 'model', 'point_history_classifier',
                                     'point_history_classifier_label.csv')

        with open(kp_label_path, encoding='utf-8-sig') as f:
            self.keypoint_classifier_labels = [row[0] for row in csv.reader(f)]

        with open(ph_label_path, encoding='utf-8-sig') as f:
            self.point_history_classifier_labels = [row[0] for row in csv.reader(f)]

        # History buffers
        self.point_history         = deque(maxlen=history_length)
        self.finger_gesture_history = deque(maxlen=history_length)

    # ── Main recognition method ──────────────────────────────
    def recognize(self, image, number=-1, mode=0):
        USE_BRECT  = True
        image      = cv.flip(image, 1)          # mirror for natural interaction
        debug_image = copy.deepcopy(image)
        gesture_id  = -1                         # default: no gesture detected

        # Convert BGR → RGB for MediaPipe
        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.hands.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                  results.multi_handedness):
                brect         = self._calc_bounding_rect(debug_image, hand_landmarks)
                landmark_list = self._calc_landmark_list(debug_image, hand_landmarks)

                # Normalize landmark coordinates
                pre_processed_landmarks    = self._pre_process_landmark(landmark_list)
                pre_processed_point_history = self._pre_process_point_history(
                    debug_image, self.point_history)

                # (Optional) save data for training
                self._logging_csv(number, mode, pre_processed_landmarks,
                                  pre_processed_point_history)

                # Classify hand sign from landmarks
                hand_sign_id = self.keypoint_classifier(pre_processed_landmarks)

                # Track index fingertip position for gesture history
                if hand_sign_id == 2:   # "Point" gesture
                    self.point_history.append(landmark_list[8])
                else:
                    self.point_history.append([0, 0])

                # Classify fingertip movement pattern
                finger_gesture_id = 0
                if len(pre_processed_point_history) == (self.history_length * 2):
                    finger_gesture_id = self.point_history_classifier(
                        pre_processed_point_history)

                self.finger_gesture_history.append(finger_gesture_id)
                most_common_fg_id = Counter(self.finger_gesture_history).most_common()

                # Draw overlays
                debug_image = self._draw_bounding_rect(USE_BRECT, debug_image, brect)
                debug_image = self._draw_landmarks(debug_image, landmark_list)
                debug_image = self._draw_info_text(
                    debug_image, brect, handedness,
                    self.keypoint_classifier_labels[hand_sign_id],
                    self.point_history_classifier_labels[most_common_fg_id[0][0]]
                )
                gesture_id = hand_sign_id
        else:
            self.point_history.append([0, 0])

        debug_image = self._draw_point_history(debug_image, self.point_history)
        return debug_image, gesture_id

    def draw_info(self, image, fps, mode, number):
        cv.putText(image, f"FPS: {fps}", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 4, cv.LINE_AA)
        cv.putText(image, f"FPS: {fps}", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv.LINE_AA)
        mode_labels = ['Logging Key Point', 'Logging Point History']
        if 1 <= mode <= 2:
            cv.putText(image, f"MODE: {mode_labels[mode - 1]}", (10, 90),
                       cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
            if 0 <= number <= 9:
                cv.putText(image, f"NUM: {number}", (10, 110),
                           cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        return image

    # ── CSV logging (for training data collection) ───────────
    def _logging_csv(self, number, mode, landmark_list, point_history_list):
        if mode == 1 and 0 <= number <= 9:
            csv_path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier', 'keypoint.csv')
            with open(csv_path, 'a', newline='') as f:
                csv.writer(f).writerow([number, *landmark_list])
        elif mode == 2 and 0 <= number <= 9:
            csv_path = os.path.join(BASE_DIR, 'model', 'point_history_classifier', 'point_history.csv')
            with open(csv_path, 'a', newline='') as f:
                csv.writer(f).writerow([number, *point_history_list])

    # ── Preprocessing helpers ─────────────────────────────────
    def _calc_bounding_rect(self, image, landmarks):
        h, w = image.shape[:2]
        points = np.array([[min(int(lm.x * w), w - 1),
                            min(int(lm.y * h), h - 1)]
                           for lm in landmarks.landmark])
        x, y, bw, bh = cv.boundingRect(points)
        return [x, y, x + bw, y + bh]

    def _calc_landmark_list(self, image, landmarks):
        h, w = image.shape[:2]
        return [[min(int(lm.x * w), w - 1),
                 min(int(lm.y * h), h - 1)]
                for lm in landmarks.landmark]

    def _pre_process_landmark(self, landmark_list):
        tmp = copy.deepcopy(landmark_list)
        base_x, base_y = tmp[0]
        tmp = [[x - base_x, y - base_y] for x, y in tmp]
        tmp = list(itertools.chain.from_iterable(tmp))
        max_val = max(map(abs, tmp))
        return [v / max_val for v in tmp]

    def _pre_process_point_history(self, image, point_history):
        h, w = image.shape[:2]
        tmp = copy.deepcopy(point_history)
        if len(tmp) == 0:
            return []
        base_x, base_y = tmp[0]
        tmp = [((x - base_x) / w, (y - base_y) / h) for x, y in tmp]
        return list(itertools.chain.from_iterable(tmp))

    # ── Drawing helpers ───────────────────────────────────────
    def _draw_point_history(self, image, point_history):
        for i, pt in enumerate(point_history):
            if pt[0] != 0 and pt[1] != 0:
                cv.circle(image, (pt[0], pt[1]), 1 + i // 2, (152, 251, 152), 2)
        return image

    def _draw_bounding_rect(self, use_brect, image, brect):
        if use_brect:
            cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]),
                         (0, 0, 0), 1)
        return image

    def _draw_landmarks(self, image, lp):
        # Connection pairs: (start_index, end_index)
        connections = [
            (2,3),(3,4),           # thumb
            (5,6),(6,7),(7,8),     # index
            (9,10),(10,11),(11,12),# middle
            (13,14),(14,15),(15,16),# ring
            (17,18),(18,19),(19,20),# little
            (0,1),(1,2),(2,5),(5,9),(9,13),(13,17),(17,0),  # palm
        ]
        for s, e in connections:
            cv.line(image, tuple(lp[s]), tuple(lp[e]), (0, 0, 0), 6)
            cv.line(image, tuple(lp[s]), tuple(lp[e]), (255, 255, 255), 2)

        for i, pt in enumerate(lp):
            r = 8 if i in (4, 8, 12, 16, 20) else 5   # larger circle at fingertips
            cv.circle(image, tuple(pt), r, (255, 255, 255), -1)
            cv.circle(image, tuple(pt), r, (0, 0, 0), 1)
        return image

    def _draw_info_text(self, image, brect, handedness, hand_sign_text, finger_gesture_text):
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22),
                     (0, 0, 0), -1)
        label = handedness.classification[0].label
        if hand_sign_text:
            label += ':' + hand_sign_text
        cv.putText(image, label, (brect[0] + 5, brect[1] - 4),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        return image


# =============================================================
# Gesture Buffer
# Accumulates recent gesture IDs and returns the most common
# only when it appears with high confidence (buffer_len - 1 times)
# =============================================================
class GestureBuffer:
    def __init__(self, buffer_len=10):
        self.buffer_len = buffer_len
        self._buffer = deque(maxlen=buffer_len)

    def add_gesture(self, gesture_id):
        self._buffer.append(gesture_id)

    def get_gesture(self):
        if not self._buffer:
            return None
        counter = Counter(self._buffer).most_common()
        # Only return gesture if it dominates the buffer (high confidence)
        if counter[0][1] >= (self.buffer_len - 1):
            self._buffer.clear()
            return counter[0][0]
        return None


# =============================================================
# Tello Gesture Controller
# Maps gesture IDs → drone RC commands
#   0: Forward   1: Stop    2: Up
#   3: Land      4: Down    5: Back
#   6: Left      7: Right
# =============================================================
class TelloGestureController:
    def __init__(self, tello: Tello):
        self.tello = tello
        self._is_landing = False
        self.left_right_velocity = 0
        self.forw_back_velocity  = 0
        self.up_down_velocity    = 0
        self.yaw_velocity        = 0

    def gesture_control(self, gesture_buffer):
        gesture_id = gesture_buffer.get_gesture()
        if gesture_id is None or self._is_landing:
            return

        print(f"GESTURE: {gesture_id}")

        if gesture_id == 0:    # Forward
            self.forw_back_velocity = 30
        elif gesture_id == 1:  # Stop — zero all velocities
            self.forw_back_velocity = self.up_down_velocity = \
                self.left_right_velocity = self.yaw_velocity = 0
        elif gesture_id == 5:  # Back
            self.forw_back_velocity = -30
        elif gesture_id == 2:  # Up
            self.up_down_velocity = 25
        elif gesture_id == 4:  # Down
            self.up_down_velocity = -25
        elif gesture_id == 3:  # Land
            self._is_landing = True
            self.forw_back_velocity = self.up_down_velocity = \
                self.left_right_velocity = self.yaw_velocity = 0
            self.tello.land()
        elif gesture_id == 6:  # Left
            self.left_right_velocity = 20
        elif gesture_id == 7:  # Right
            self.left_right_velocity = -20
        elif gesture_id == -1: # No hand detected — stop
            self.forw_back_velocity = self.up_down_velocity = \
                self.left_right_velocity = self.yaw_velocity = 0

        self.tello.send_rc_control(
            self.left_right_velocity, self.forw_back_velocity,
            self.up_down_velocity, self.yaw_velocity
        )


# =============================================================
# Tello Keyboard Controller
# WASD: forward/back/left/right  Q/E: yaw  R/F: up/down
# =============================================================
class TelloKeyboardController:
    def __init__(self, tello: Tello):
        self.tello = tello

    def control(self, key):
        if   key == ord('w'): self.tello.move_forward(30)
        elif key == ord('s'): self.tello.move_back(30)
        elif key == ord('a'): self.tello.move_left(30)
        elif key == ord('d'): self.tello.move_right(30)
        elif key == ord('e'): self.tello.rotate_clockwise(30)
        elif key == ord('q'): self.tello.rotate_counter_clockwise(30)
        elif key == ord('r'): self.tello.move_up(30)
        elif key == ord('f'): self.tello.move_down(30)


# =============================================================
# Main
# =============================================================
def main():
    KEYBOARD_CONTROL = IS_KEYBOARD
    WRITE_CONTROL    = False
    in_flight        = False
    battery_status   = -1

    # Drone setup
    tello = Tello()
    tello.connect()
    print(f"Battery: {tello.get_battery()}%")
    tello.streamon()
    cap = tello.get_frame_read()

    # Controllers
    gesture_controller  = TelloGestureController(tello)
    keyboard_controller = TelloKeyboardController(tello)

    # Gesture recognition & buffer
    gesture_detector = GestureRecognition(
        use_static_image_mode=USE_STATIC_IMAGE_MODE,
        min_detection_confidence=MIN_DETECTION_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF,
        history_length=BUFFER_LEN,
    )
    gesture_buffer = GestureBuffer(buffer_len=BUFFER_LEN)

    cv_fps_calc = CvFpsCalc(buffer_len=10)
    mode = 0
    number = -1

    # Battery refresh thread (every 10 seconds, not every frame)
    def refresh_battery():
        nonlocal battery_status
        while True:
            try:
                battery_status = tello.get_battery()   # fix: returns int, not string
            except Exception:
                pass
            threading.Event().wait(10)

    threading.Thread(target=refresh_battery, daemon=True).start()

    while True:
        fps = cv_fps_calc.get()
        key = cv.waitKey(1) & 0xFF

        # ── Key handling ─────────────────────────────────────
        if key == 27:           # ESC → quit
            break
        elif key == 32:         # SPACE → takeoff / land
            if not in_flight:
                tello.takeoff()
                in_flight = True
            else:
                tello.land()
                in_flight = False
        elif key == ord('k'):   # keyboard mode
            KEYBOARD_CONTROL = True
            WRITE_CONTROL    = False
            mode = 0
            tello.send_rc_control(0, 0, 0, 0)
        elif key == ord('g'):   # gesture mode
            KEYBOARD_CONTROL = False
        elif key == ord('n'):   # data logging mode
            WRITE_CONTROL    = True
            KEYBOARD_CONTROL = True
            mode = 1

        if WRITE_CONTROL and 48 <= key <= 57:   # 0-9 to label gesture class
            number = key - 48
        else:
            number = -1

        # ── Drone control ─────────────────────────────────────
        if in_flight:
            if KEYBOARD_CONTROL:
                keyboard_controller.control(key)
            else:
                gesture_controller.gesture_control(gesture_buffer)

        # ── Frame processing ──────────────────────────────────
        image = cap.frame
        debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        gesture_buffer.add_gesture(gesture_id)

        debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        # ── HUD overlay ───────────────────────────────────────
        mode_text = "KEYBOARD" if KEYBOARD_CONTROL else "GESTURE"
        flight_text = "FLYING" if in_flight else "LANDED"
        cv.putText(debug_image, f"Battery: {battery_status}%", (5, HEIGHT - 35),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv.putText(debug_image, f"Mode: {mode_text}  |  {flight_text}", (5, HEIGHT - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv.imshow('Tello Gesture Recognition', debug_image)

    # Cleanup
    if in_flight:
        tello.land()
    tello.end()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
