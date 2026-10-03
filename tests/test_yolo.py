"""
Phase 2: YOLO test.
Loads a pretrained YOLO model and runs it on a sample image.
Saves the result with bounding boxes to data/yolo_test_result.jpg
"""

import sys
from pathlib import Path

from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "yolov8n.pt"
IMAGE_PATH = PROJECT_ROOT / "data" / "test_people.jpg"
OUTPUT_PATH = PROJECT_ROOT / "data" / "yolo_test_result.jpg"


def main():
    # 1. Check the test image exists
    if not IMAGE_PATH.exists():
        print(f"[ERROR] Test image not found: {IMAGE_PATH}")
        print("Put any photo containing people at that path.")
        sys.exit(1)

    # 2. Load the model (downloads yolov8n.pt on first run if missing)
    print(f"[INFO] Loading model: {MODEL_PATH}")
    MODEL_PATH.parent.mkdir(exist_ok=True)
    try:
        model = YOLO(str(MODEL_PATH))
    except Exception as e:
        print(f"[ERROR] Could not load YOLO model: {e}")
        sys.exit(1)

    # 3. Run detection. classes=[0] means ONLY the 'person' class (COCO id 0).
    results = model.predict(source=str(IMAGE_PATH), classes=[0], conf=0.4, verbose=False)
    result = results[0]

    person_count = len(result.boxes)
    print(f"[OK] Detected people: {person_count}")

    for i, box in enumerate(result.boxes):
        confidence = float(box.conf[0])
        print(f"  person {i + 1}: confidence {confidence:.2f}")

    # 4. Save annotated image
    result.save(filename=str(OUTPUT_PATH))
    print(f"[OK] Annotated image saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()