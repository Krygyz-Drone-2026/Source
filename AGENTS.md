# Repository Guidelines

## Project Structure & Module Organization
This repository is organized as standalone Python lab exercises for Tello drone control and computer vision. Root-level files such as `Lab-02.py`, `Lab-36.py`, and `Lab-41.py` are individual examples that can be run directly. `Lab-42/` contains the TensorFlow Lite gesture-control variant and its `model/` assets; `Lab-42-Torch/` contains the PyTorch port plus `convert_models.py` for model conversion. Large binary assets such as `yolov8n.pt` and `drone.jpeg` stay at the repository root.

## Build, Test, and Development Commands
There is no single build system; run scripts directly with Python from the repository root.

```powershell
python .\Lab-36.py
python .\Lab-42\Lab-42.py
python .\Lab-42-Torch\Lab-42.py
python .\Lab-42-Torch\convert_models.py .\Lab-42-Torch .\Lab-42\model
```

Install only the dependencies needed for the lab you are editing. Common packages in this repo include `djitellopy`, `opencv-python`, `mediapipe`, `ultralytics`, `cvzone`, `torch`, `onnx`, and `tflite2onnx`.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, descriptive snake_case names for functions and variables, and PascalCase for classes such as `KeyPointClassifier`. Keep new lab files aligned with the current naming pattern: `Lab-XX.py` or `Lab-XX-Variant.py`. Prefer small, runnable scripts over cross-file abstractions unless a shared helper is clearly reused.

## Testing Guidelines
This repository does not currently include `pytest` or `unittest` suites. Validate changes by running the affected script locally and confirming the expected drone, camera, or model behavior. For vision-only changes, prefer tests that can run without live flight hardware, and document any hardware dependency in your change notes.

## Commit & Pull Request Guidelines
Local `.git` metadata is not present in this workspace, so no historical commit convention can be derived here. Use short, imperative commit subjects such as `Add Torch model conversion notes` or `Fix Tello video frame handling`. Pull requests should state which lab files changed, list required packages or model files, and include screenshots or console output when UI, vision, or inference behavior changes.

## Security & Configuration Tips
Do not commit Wi-Fi credentials, drone IP overrides, or local environment paths. Keep large model files in their existing directories, and avoid hard-coded absolute paths because this repository already works around Windows paths containing spaces or Korean characters.
