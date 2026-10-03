"""
Phase 3: Live person detection and counting from the webcam.
Press 'q' in the video window to quit.
"""

import sys
import time
from pathlib import Path

import cv2

# Allow importing from the backend folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from detector import PersonDetector  # noqa: E402

CAMERA_SOURCE = 0


def main():
    print("[INFO] Loading YOLO model...")
    detector = PersonDetector()

    if isinstance(CAMERA_SOURCE, int):
        cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(CAMERA_SOURCE)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera: {CAMERA_SOURCE}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("[OK] Running. Press 'q' in the video window to quit.")

    frame_count = 0
    start = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] Failed to read frame.")
            break

        count, annotated = detector.detect(frame)

        frame_count += 1
        elapsed = time.time() - start
        if elapsed >= 1.0:
            fps = frame_count / elapsed
            frame_count = 0
            start = time.time()

        cv2.putText(
            annotated,
            f"Passengers: {count}  |  FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2,
        )
        cv2.imshow("Phase 3 - Live Detection (press q to quit)", annotated)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[DONE]")


if __name__ == "__main__":
    main()