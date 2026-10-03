"""
Phase 1: Webcam test.
Opens the camera, shows live video, prints resolution and FPS.
Press 'q' in the video window to quit.
"""

import sys
import time

import cv2

# 0 = first camera (/dev/video0).
# Later this can be an RTSP URL string, e.g. "rtsp://user:pass@192.168.1.10/stream"
CAMERA_SOURCE = 0


def main():
    # CAP_V4L2 explicitly uses the Linux Video4Linux2 backend (integer indexes only).
    if isinstance(CAMERA_SOURCE, int):
        cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(CAMERA_SOURCE)

    if not cap.isOpened():
        print(f"[ERROR] Could not open camera source: {CAMERA_SOURCE}")
        print("Try a different index (0, 1, 2, 3...) or check: v4l2-ctl --list-devices")
        sys.exit(1)

    # Ask for MJPG at 640x480, 30 fps (your camera supports this natively)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[OK] Camera opened: {CAMERA_SOURCE}")
    print(f"[INFO] Resolution: {width}x{height}")
    print("[INFO] Press 'q' in the video window to quit.")

    frame_count = 0
    start = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[ERROR] Failed to read frame (camera disconnected?).")
            break

        frame_count += 1
        elapsed = time.time() - start
        if elapsed >= 1.0:
            fps = frame_count / elapsed
            frame_count = 0
            start = time.time()

        cv2.putText(
            frame,
            f"FPS: {fps:.1f}  |  {width}x{height}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Phase 1 - Camera Test (press q to quit)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[DONE] Camera released.")


if __name__ == "__main__":
    main()
