"""
Phase 4b: Live detection + occupancy + crowd level overlay.
Press 'q' to quit.
"""

import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from crowd import CountSmoother, calculate_occupancy, classify_crowd  # noqa: E402
from detector import PersonDetector  # noqa: E402

CAMERA_SOURCE = 0
BUS_CAPACITY = 4  # small on purpose so you can see every level with a few people

# BGR colors for drawing
COLORS = {
    "green": (0, 200, 0),
    "yellow": (0, 220, 255),
    "orange": (0, 140, 255),
    "red": (0, 0, 255),
}


def main():
    detector = PersonDetector()
    smoother = CountSmoother()

    cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera: {CAMERA_SOURCE}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[OK] Running. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] Failed to read frame.")
            break

        raw_count, annotated = detector.detect(frame)
        count = smoother.update(raw_count)
        occupancy = calculate_occupancy(count, BUS_CAPACITY)
        label, color_name = classify_crowd(occupancy)
        color = COLORS[color_name]

        cv2.rectangle(annotated, (0, 0), (640, 95), (0, 0, 0), -1)
        cv2.putText(annotated, f"Passengers: {count} (raw {raw_count})", (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated, f"Occupancy: {occupancy}% of {BUS_CAPACITY}", (10, 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(annotated, f"Crowd: {label}", (10, 88),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow("Phase 4 - Occupancy (press q to quit)", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()