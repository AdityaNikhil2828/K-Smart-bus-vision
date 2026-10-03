"""
detector.py
Person detection using YOLO. Only the COCO 'person' class is counted.
"""

from pathlib import Path

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "yolov8n.pt"

PERSON_CLASS_ID = 0      # COCO class 0 = person
CONFIDENCE = 0.6         # raise to remove false positives, lower to catch more people
IMAGE_SIZE = 640         # YOLO input size; lower (e.g. 480) = faster, less accurate


class PersonDetector:
    def __init__(self, model_path=MODEL_PATH, confidence=CONFIDENCE):
        self.confidence = confidence
        try:
            self.model = YOLO(str(model_path))
        except Exception as e:
            raise RuntimeError(f"Could not load YOLO model at {model_path}: {e}")

    def detect(self, frame):
        """
        Run detection on one frame (a BGR numpy array from OpenCV).
        Returns (person_count, annotated_frame).
        """
        results = self.model.predict(
            source=frame,
            classes=[PERSON_CLASS_ID],
            conf=self.confidence,
            imgsz=IMAGE_SIZE,
            verbose=False,
        )
        result = results[0]
        person_count = len(result.boxes)

        annotated = frame.copy()
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated,
                f"person {conf:.2f}",
                (x1, max(y1 - 8, 15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        return person_count, annotated