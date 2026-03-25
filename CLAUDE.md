# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Standalone Python lab exercises for DJI Tello drone control and computer vision. Labs progress from basic flight commands to advanced CV-based autonomous tracking. Each `Lab-XX.py` file is a self-contained script run directly from this directory.

## Running Scripts

No build system. Run scripts directly from the repo root:

```bash
python Lab-36.py
python Lab-42/Lab-42.py
python Lab-42-Torch/Lab-42.py
python Lab-42-Torch/convert_models.py ./Lab-42-Torch ./Lab-42/model
```

Most labs require the Tello connected via Wi-Fi (192.168.10.1). Labs 13, 14, 17, 18 can run offline (webcam or static image only).

## Dependencies

Install only what the target lab needs:

```bash
pip install djitellopy opencv-python cvzone ultralytics mediapipe torch onnx tflite2onnx
```

## Lab Progression

| Lab | Topic |
|-----|-------|
| Lab-02 | Takeoff / land |
| Lab-07-01/02 | Vertical bounce movements |
| Lab-08 | Complex waypoint flight (`go_xyz_speed`) |
| Lab-10 | Menu-driven console control |
| Lab-10-Simple-GUI-01/02/03 | Tkinter GUI controller (progressively richer) |
| Lab-11 | RC control with speed adjustment |
| Lab-12 / Lab-12-01 | 3D waypoint movement |
| Lab-13 / Lab-14 | Static image loading and display (OpenCV only) |
| Lab-17 | Webcam capture and display (OpenCV only) |
| Lab-18 | Webcam capture with `VideoWriter` save to `output.avi` |
| Lab-21 | Keyboard control using discrete move commands (`move_forward`, etc.) |
| Lab-21-01 | Keyboard control using continuous `send_rc_control` |
| Lab-34 | Haar Cascade face detection on drone feed |
| Lab-36 | Forward/backward control by detected face area |
| Lab-39 | Yaw rotation to keep face horizontally centered |
| Lab-40 | YOLOv8 person tracking with EMA smoothing |
| Lab-41 | Full 3-axis PID face tracking (cvzone FaceDetector + LivePlot) |
| Lab-42.py | MediaPipe hand gesture → drone commands (TFLite, root-level) |
| Lab-42/ | Same as Lab-42.py; bytes-based model loading (Windows fix) |
| Lab-42-Torch/ | PyTorch gesture variant; `convert_models.py` converts TFLite→ONNX→PT |

## Two Drone Movement Approaches

**Discrete commands** (Lab-21) — blocking, waits for completion:
```python
tello.move_forward(30)   # cm
tello.rotate_clockwise(30)  # degrees
```

**Continuous RC control** (Lab-21-01, Lab-36+) — non-blocking, call each frame:
```python
tello.send_rc_control(lr, fb, ud, yaw)  # each -100 to 100
```
Labs from Lab-36 onward use `send_rc_control` inside the CV loop for responsive tracking.

## PID Tracking Pattern (Lab-41)

Three independent PID axes fed into `send_rc_control`:
- **Yaw**: center face horizontally
- **Throttle (ud)**: center face vertically
- **Forward/back (fb)**: maintain target face area (~12 000 px²)

## Lab-42 Gesture Mapping

`0`=Forward, `1`=Stop, `2`=Up, `3`=Land, `4`=Down, `5`=Back, `6`=Left, `7`=Right
Modes: `k`=keyboard, `g`=gesture, `n`=data logging — `SPACE`=takeoff/land, `ESC`=quit

## Coding Conventions

- 4-space indentation, snake_case functions/variables, PascalCase classes (e.g., `KeyPointClassifier`)
- New lab files: `Lab-XX.py` or `Lab-XX-Variant.py`
- Keep scripts self-contained; avoid cross-file abstractions unless a helper is clearly reused across labs
- Avoid hard-coded absolute paths — the repo path contains spaces and Korean characters, which breaks some tools on Windows

## Assets

- `yolov8n.pt` — YOLOv8 nano weights (root-level)
- `drone.jpeg` — sample image used by Lab-13/14
- `output.avi` — written by Lab-18 at runtime
- `Lab-42/model/` and `Lab-42-Torch/model/` — TFLite / ONNX / PT gesture model files
