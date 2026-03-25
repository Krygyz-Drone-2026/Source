# =============================================================
# convert_models.py
# TFLite → ONNX → PyTorch model conversion script
# Run once before using Lab-42.py (PyTorch version)
# =============================================================

import os
import tflite2onnx
import onnx
import onnx2torch
import torch

# Paths are passed as arguments to avoid Korean/space path issues
import sys
BASE_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
SRC_DIR  = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE_DIR, '..', 'Lab-42', 'model')
DST_DIR  = os.path.join(BASE_DIR, 'model')

models = [
    {
        'tflite': os.path.join(SRC_DIR, 'keypoint_classifier', 'keypoint_classifier.tflite'),
        'onnx':   os.path.join(DST_DIR, 'keypoint_classifier', 'keypoint_classifier.onnx'),
        'pt':     os.path.join(DST_DIR, 'keypoint_classifier', 'keypoint_classifier.pt'),
        'name':   'KeyPointClassifier',
    },
    {
        'tflite': os.path.join(SRC_DIR, 'point_history_classifier', 'point_history_classifier.tflite'),
        'onnx':   os.path.join(DST_DIR, 'point_history_classifier', 'point_history_classifier.onnx'),
        'pt':     os.path.join(DST_DIR, 'point_history_classifier', 'point_history_classifier.pt'),
        'name':   'PointHistoryClassifier',
    },
]

for m in models:
    print(f"\n[{m['name']}]")

    # Step 1: TFLite → ONNX
    print(f"  TFLite → ONNX ...")
    tflite2onnx.convert(m['tflite'], m['onnx'])
    print(f"  Saved: {m['onnx']}")

    # Step 2: ONNX → PyTorch
    print(f"  ONNX → PyTorch ...")
    onnx_model = onnx.load(m['onnx'])
    pt_model = onnx2torch.convert(onnx_model)
    pt_model.eval()
    torch.save(pt_model, m['pt'])
    print(f"  Saved: {m['pt']}")

print("\nConversion complete!")
