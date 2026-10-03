"""
camera.py
Reads a camera in a background thread, runs person detection,
and keeps the latest annotated frame + passenger count.

CAMERA_SOURCE:
    0                         -> USB webcam (/dev/video0)
    "rtsp://user:pass@ip/..." -> IP camera / CCTV / NVR stream
"""

import threading
import time

import cv2

from crowd import CountSmoother
from detector import PersonDetector

CAMERA_SOURCE = 0
RETRY_SECONDS = 3       # wait before trying to reopen a lost camera
JPEG_QUALITY = 80


class CameraStream:
    def __init__(self, source=CAMERA_SOURCE):
        self.source = source
        self.detector = None
        self.detector_error = None
        self.smoother = CountSmoother()

        self._lock = threading.Lock()
        self._jpeg = None          # latest annotated frame, JPEG bytes
        self._raw_count = 0
        self._count = 0            # smoothed count
        self._online = False
        self._last_update = None
        self._stop = threading.Event()
        self._thread = None

    # ---------- public API ----------
    def start(self):
        try:
            self.detector = PersonDetector()
        except Exception as e:
            # Do not crash the server; report the error via status
            self.detector_error = str(e)
            print(f"[ERROR] YOLO unavailable: {e}")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)

    def get_state(self):
        with self._lock:
            return {
                "passengers": self._count,
                "raw_count": self._raw_count,
                "camera_online": self._online,
                "detector_error": self.detector_error,
                "last_updated": self._last_update,
            }

    def get_jpeg(self):
        with self._lock:
            return self._jpeg

    def mjpeg_generator(self):
        """Yields frames for a multipart MJPEG HTTP stream."""
        last = None
        while not self._stop.is_set():
            jpeg = self.get_jpeg()
            if jpeg is not None and jpeg is not last:
                last = jpeg
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            time.sleep(0.04)

    # ---------- internals ----------
    def _open(self):
        if isinstance(self.source, int):
            cap = cv2.VideoCapture(self.source, cv2.CAP_V4L2)
        else:
            cap = cv2.VideoCapture(self.source)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            return cap
        cap.release()
        return None

    def _set_offline(self):
        with self._lock:
            self._online = False
            self._jpeg = None

    def _run(self):
        while not self._stop.is_set():
            cap = self._open()
            if cap is None:
                print(f"[WARN] Camera {self.source} unavailable, retrying...")
                self._set_offline()
                time.sleep(RETRY_SECONDS)
                continue

            print(f"[OK] Camera {self.source} opened.")
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    print("[WARN] Lost camera frame.")
                    break

                raw_count = 0
                annotated = frame
                if self.detector is not None:
                    try:
                        raw_count, annotated = self.detector.detect(frame)
                    except Exception as e:
                        self.detector_error = str(e)
                        print(f"[ERROR] Detection failed: {e}")

                count = self.smoother.update(raw_count)
                ok_jpg, buf = cv2.imencode(
                    ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
                )
                if ok_jpg:
                    with self._lock:
                        self._jpeg = buf.tobytes()
                        self._raw_count = raw_count
                        self._count = count
                        self._online = True
                        self._last_update = time.strftime("%H:%M:%S")

            cap.release()
            self._set_offline()
            time.sleep(RETRY_SECONDS)