# =============================================================
# Lab-42 (PyTorch version): Tello Gesture Control
# Source: https://github.com/kinivi/tello-gesture-control
#
# Changes from Lab-42 (TFLite):
#   - ai_edge_litert  →  torch (PyTorch inference)
#   - .tflite models  →  .pt models (converted via tflite2onnx + onnx2torch)
#
# Controls:
#   SPACE  : takeoff / land
#   k      : keyboard mode (WASD / Q,E,R,F)
#   g      : gesture mode
#   n      : data logging mode
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
import torch
from djitellopy import Tello

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Configuration ─────────────────────────────────────────────
DEVICE                 = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
WIDTH, HEIGHT          = 960, 720
IS_KEYBOARD            = True
USE_STATIC_IMAGE_MODE  = False
MIN_DETECTION_CONF     = 0.7
MIN_TRACKING_CONF      = 0.7
BUFFER_LEN             = 10   # GestureBuffer confidence window
HISTORY_LEN            = 16   # point history length (model input = 16×2 = 32)

print(f"Using device: {DEVICE}")

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
        return round(1000.0 / (sum(self._difftimes) / len(self._difftimes)), 2)


# =============================================================
# Model: KeyPoint Classifier (PyTorch)
# Input : 42 normalized landmark values (21 hand points × 2)
# Output: gesture class index (0~7)
# =============================================================
class KeyPointClassifier:
    def __init__(self):
        model_path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier',
                                  'keypoint_classifier.pt')
        # torch.save saved the full model object (onnx2torch converted)
        self.model = torch.load(model_path, map_location=DEVICE, weights_only=False)
        self.model.eval()

    def __call__(self, landmark_list):
        # landmark_list: list of 42 floats
        x = torch.tensor([landmark_list], dtype=torch.float32).to(DEVICE)
        with torch.no_grad():
            output = self.model(x)
        return int(torch.argmax(output, dim=1).item())


# =============================================================
# Model: Point History Classifier (PyTorch)
# Input : 32 values — trajectory of index fingertip (16 points × 2)
# Output: finger gesture class index (0~3)
# =============================================================
class PointHistoryClassifier:
    def __init__(self, score_th=0.5, invalid_value=0):
        model_path = os.path.join(BASE_DIR, 'model', 'point_history_classifier',
                                  'point_history_classifier.pt')
        self.model = torch.load(model_path, map_location=DEVICE, weights_only=False)
        self.model.eval()
        self.score_th      = score_th
        self.invalid_value = invalid_value

    def __call__(self, point_history):
        x = torch.tensor([point_history], dtype=torch.float32).to(DEVICE)
        with torch.no_grad():
            output = self.model(x)
        probs = torch.softmax(output, dim=1).squeeze()
        result_index = int(torch.argmax(probs).item())
        # Return invalid if confidence below threshold
        if probs[result_index].item() < self.score_th:
            result_index = self.invalid_value
        return result_index


# =============================================================
# Gesture Recognition
# =============================================================
class GestureRecognition:
    def __init__(self, use_static_image_mode=False,
                 min_detection_confidence=0.7,
                 min_tracking_confidence=0.7,
                 history_length=16):
        self.history_length = history_length

        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            static_image_mode=use_static_image_mode,
            max_num_hands=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

        self.keypoint_classifier      = KeyPointClassifier()
        self.point_history_classifier = PointHistoryClassifier()

        kp_label_path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier',
                                     'keypoint_classifier_label.csv')
        ph_label_path = os.path.join(BASE_DIR, 'model', 'point_history_classifier',
                                     'point_history_classifier_label.csv')

        with open(kp_label_path, encoding='utf-8-sig') as f:
            self.keypoint_classifier_labels = [row[0] for row in csv.reader(f)]
        with open(ph_label_path, encoding='utf-8-sig') as f:
            self.point_history_classifier_labels = [row[0] for row in csv.reader(f)]

        self.point_history          = deque(maxlen=history_length)
        self.finger_gesture_history = deque(maxlen=history_length)

    def recognize(self, image, number=-1, mode=0):
        image       = cv.flip(image, 1)
        debug_image = copy.deepcopy(image)
        gesture_id  = -1

        image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False
        results = self.hands.process(image_rgb)
        image_rgb.flags.writeable = True

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                                  results.multi_handedness):
                brect         = self._calc_bounding_rect(debug_image, hand_landmarks)
                landmark_list = self._calc_landmark_list(debug_image, hand_landmarks)

                pre_processed_landmarks     = self._pre_process_landmark(landmark_list)
                pre_processed_point_history = self._pre_process_point_history(
                    debug_image, self.point_history)

                self._logging_csv(number, mode, pre_processed_landmarks,
                                  pre_processed_point_history)

                hand_sign_id = self.keypoint_classifier(pre_processed_landmarks)

                if hand_sign_id == 2:
                    self.point_history.append(landmark_list[8])
                else:
                    self.point_history.append([0, 0])

                finger_gesture_id = 0
                if len(pre_processed_point_history) == (self.history_length * 2):
                    finger_gesture_id = self.point_history_classifier(
                        pre_processed_point_history)

                self.finger_gesture_history.append(finger_gesture_id)
                most_common_fg_id = Counter(self.finger_gesture_history).most_common()

                debug_image = self._draw_bounding_rect(debug_image, brect)
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

    def _logging_csv(self, number, mode, landmark_list, point_history_list):
        if mode == 1 and 0 <= number <= 9:
            path = os.path.join(BASE_DIR, 'model', 'keypoint_classifier', 'keypoint.csv')
            with open(path, 'a', newline='') as f:
                csv.writer(f).writerow([number, *landmark_list])
        elif mode == 2 and 0 <= number <= 9:
            path = os.path.join(BASE_DIR, 'model', 'point_history_classifier', 'point_history.csv')
            with open(path, 'a', newline='') as f:
                csv.writer(f).writerow([number, *point_history_list])

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

    def _draw_point_history(self, image, point_history):
        for i, pt in enumerate(point_history):
            if pt[0] != 0 and pt[1] != 0:
                cv.circle(image, (pt[0], pt[1]), 1 + i // 2, (152, 251, 152), 2)
        return image

    def _draw_bounding_rect(self, image, brect):
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]), (0, 0, 0), 1)
        return image

    def _draw_landmarks(self, image, lp):
        connections = [
            (2,3),(3,4),(5,6),(6,7),(7,8),(9,10),(10,11),(11,12),
            (13,14),(14,15),(15,16),(17,18),(18,19),(19,20),
            (0,1),(1,2),(2,5),(5,9),(9,13),(13,17),(17,0),
        ]
        for s, e in connections:
            cv.line(image, tuple(lp[s]), tuple(lp[e]), (0, 0, 0), 6)
            cv.line(image, tuple(lp[s]), tuple(lp[e]), (255, 255, 255), 2)
        for i, pt in enumerate(lp):
            r = 8 if i in (4, 8, 12, 16, 20) else 5
            cv.circle(image, tuple(pt), r, (255, 255, 255), -1)
            cv.circle(image, tuple(pt), r, (0, 0, 0), 1)
        return image

    def _draw_info_text(self, image, brect, handedness, hand_sign_text, finger_gesture_text):
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
        label = handedness.classification[0].label
        if hand_sign_text:
            label += ':' + hand_sign_text
        cv.putText(image, label, (brect[0] + 5, brect[1] - 4),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
        return image


# =============================================================
# Gesture Buffer
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
        if counter[0][1] >= (self.buffer_len - 1):
            self._buffer.clear()
            return counter[0][0]
        return None


# =============================================================
# Tello Gesture Controller
#   0:Forward  1:Stop  2:Up  3:Land  4:Down  5:Back  6:Left  7:Right
# =============================================================
class TelloGestureController:
    def __init__(self, tello: Tello):
        self.tello = tello
        self._is_landing        = False
        self.left_right_velocity = 0
        self.forw_back_velocity  = 0
        self.up_down_velocity    = 0
        self.yaw_velocity        = 0

    def gesture_control(self, gesture_buffer):
        gesture_id = gesture_buffer.get_gesture()
        if gesture_id is None or self._is_landing:
            return
        print(f"GESTURE: {gesture_id}")
        if   gesture_id == 0: self.forw_back_velocity = 30
        elif gesture_id == 1: self.forw_back_velocity = self.up_down_velocity = self.left_right_velocity = self.yaw_velocity = 0
        elif gesture_id == 5: self.forw_back_velocity = -30
        elif gesture_id == 2: self.up_down_velocity = 25
        elif gesture_id == 4: self.up_down_velocity = -25
        elif gesture_id == 3:
            self._is_landing = True
            self.forw_back_velocity = self.up_down_velocity = self.left_right_velocity = self.yaw_velocity = 0
            self.tello.land()
        elif gesture_id == 6: self.left_right_velocity = 20
        elif gesture_id == 7: self.left_right_velocity = -20
        elif gesture_id == -1: self.forw_back_velocity = self.up_down_velocity = self.left_right_velocity = self.yaw_velocity = 0
        self.tello.send_rc_control(self.left_right_velocity, self.forw_back_velocity,
                                   self.up_down_velocity, self.yaw_velocity)


# =============================================================
# Tello Keyboard Controller
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

    tello = Tello()
    tello.connect()
    print(f"Battery: {tello.get_battery()}%")
    tello.streamon()
    cap = tello.get_frame_read()

    gesture_controller  = TelloGestureController(tello)
    keyboard_controller = TelloKeyboardController(tello)

    gesture_detector = GestureRecognition(
        use_static_image_mode=USE_STATIC_IMAGE_MODE,
        min_detection_confidence=MIN_DETECTION_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF,
        history_length=HISTORY_LEN,
    )
    gesture_buffer = GestureBuffer(buffer_len=BUFFER_LEN)
    cv_fps_calc    = CvFpsCalc(buffer_len=10)
    mode   = 0
    number = -1

    def refresh_battery():
        nonlocal battery_status
        while True:
            try:
                battery_status = tello.get_battery()
            except Exception:
                pass
            threading.Event().wait(10)

    threading.Thread(target=refresh_battery, daemon=True).start()

    while True:
        fps = cv_fps_calc.get()
        key = cv.waitKey(1) & 0xFF

        if key == 27:           # ESC
            break
        elif key == 32:         # SPACE: takeoff / land
            if not in_flight:
                tello.takeoff()
                in_flight = True
            else:
                tello.land()
                in_flight = False
        elif key == ord('k'):
            KEYBOARD_CONTROL = True
            WRITE_CONTROL    = False
            mode = 0
            tello.send_rc_control(0, 0, 0, 0)
        elif key == ord('g'):
            KEYBOARD_CONTROL = False
        elif key == ord('n'):
            WRITE_CONTROL    = True
            KEYBOARD_CONTROL = True
            mode = 1

        number = (key - 48) if (WRITE_CONTROL and 48 <= key <= 57) else -1

        if in_flight:
            if KEYBOARD_CONTROL:
                keyboard_controller.control(key)
            else:
                gesture_controller.gesture_control(gesture_buffer)

        image = cap.frame
        debug_image, gesture_id = gesture_detector.recognize(image, number, mode)
        gesture_buffer.add_gesture(gesture_id)
        debug_image = gesture_detector.draw_info(debug_image, fps, mode, number)

        mode_text   = "KEYBOARD" if KEYBOARD_CONTROL else "GESTURE"
        flight_text = "FLYING"   if in_flight        else "LANDED"
        cv.putText(debug_image, f"Battery: {battery_status}%", (5, HEIGHT - 35),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv.putText(debug_image, f"Mode: {mode_text}  |  {flight_text}", (5, HEIGHT - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

        cv.imshow('Tello Gesture Recognition (PyTorch)', debug_image)

    if in_flight:
        tello.land()
    tello.end()
    cv.destroyAllWindows()


if __name__ == '__main__':
    main()
