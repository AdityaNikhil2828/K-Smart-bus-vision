"""
detector.py
Person detection using YOLO. Only the COCO 'person' class is counted.
Faces within each detected person's box are blurred for privacy.
"""

from pathlib import Path

import cv2
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "yolov8n.pt"

PERSON_CLASS_ID = 0      # COCO class 0 = person
CONFIDENCE = 0.6         # raise to remove false positives, lower to catch more people
IMAGE_SIZE = 640         # YOLO input size; lower (e.g. 480) = faster, less accurate

BLUR_FACES = True        # set False to disable face blurring
FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
BLUR_STRENGTH = 51       # must be odd; higher = stronger blur


class PersonDetector:
    def __init__(self, model_path=MODEL_PATH, confidence=CONFIDENCE):
        self.confidence = confidence
        try:
            self.model = YOLO(str(model_path))
        except Exception as e:
            raise RuntimeError(f"Could not load YOLO model at {model_path}: {e}")

        self.face_cascade = None
        if BLUR_FACES:
            cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
            if not cascade.empty():
                self.face_cascade = cascade
            else:
                print("[WARN] Could not load face cascade; face blurring disabled.")

    def _blur_faces_in_region(self, annotated, x1, y1, x2, y2):
        """Detects and blurs faces within a person's bounding box region."""
        if self.face_cascade is None:
            return

        h, w = annotated.shape[:2]
        rx1, ry1 = max(0, x1), max(0, y1)
        rx2, ry2 = min(w, x2), min(h, y2)
        if rx2 <= rx1 or ry2 <= ry1:
            return

        region = annotated[ry1:ry2, rx1:rx2]
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
        )

        for (fx, fy, fw, fh) in faces:
            pad_x, pad_y = int(fw * 0.15), int(fh * 0.2)
            bx1 = max(0, fx - pad_x)
            by1 = max(0, fy - pad_y)
            bx2 = min(region.shape[1], fx + fw + pad_x)
            by2 = min(region.shape[0], fy + fh + pad_y)

            face_region = region[by1:by2, bx1:bx2]
            if face_region.size == 0:
                continue
            blurred = cv2.GaussianBlur(face_region, (BLUR_STRENGTH, BLUR_STRENGTH), 0)
            region[by1:by2, bx1:bx2] = blurred

    def detect(self, frame):
        """
        Run detection on one frame (a BGR numpy array from OpenCV).
        Returns (person_count, annotated_frame).
        Faces within each detected person's box are blurred for privacy.
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

            self._blur_faces_in_region(annotated, x1, y1, x2, y2)

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