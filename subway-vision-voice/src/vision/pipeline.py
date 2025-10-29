"""Vision pipeline to capture frames and emit gestures."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

from ..core.events import GestureEvent
from .gestures import GestureDetector
from .hud import HeadsUpDisplay

LOGGER = logging.getLogger(__name__)


@dataclass
class VisionPipeline:
    cfg
    event_cb: Callable[[GestureEvent], None]
    hud: Optional[HeadsUpDisplay] = None
    frame_limit: Optional[int] = None

    def __post_init__(self) -> None:
        self.detector = GestureDetector(self.cfg.gesture)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if cv2 is None:
            LOGGER.error("OpenCV not available, cannot start vision pipeline")
            return
        camera_index = int(self.cfg.camera.get("index", 0))
        width, height = self.cfg.camera.get("processing_resolution", [640, 360])
        self._cap = cv2.VideoCapture(camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="VisionLoop", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        self._cleanup()

    def _loop(self) -> None:
        assert cv2 is not None
        last_emit = 0.0
        processed = 0
        while not self._stop.is_set():
            ret, frame = self._cap.read()
            if not ret:
                LOGGER.warning("Camera read failed, retrying...")
                time.sleep(0.1)
                continue
            events = self.detector.process_frame(frame)
            if self.hud:
                self.hud.update(frame, events)
            for event in events:
                self.event_cb(event)
            if not events:
                time.sleep(0.005)
            processed += 1
            if self.frame_limit and processed >= self.frame_limit:
                LOGGER.info("Frame limit reached (%s), stopping vision pipeline", self.frame_limit)
                self._stop.set()
                break
        self._cleanup()

    def calibrate(self, seconds: int = 10) -> dict:
        if cv2 is None:
            raise RuntimeError("OpenCV is required for calibration")
        camera_index = int(self.cfg.camera.get("index", 0))
        cap = cv2.VideoCapture(camera_index)
        frames = []
        start = time.time()
        while time.time() - start < seconds:
            ret, frame = cap.read()
            if not ret:
                continue
            frames.append(frame)
        cap.release()
        return self.detector.calibrate(frames)

    def _cleanup(self) -> None:
        if hasattr(self, "_cap") and self._cap:
            self._cap.release()
            self._cap = None
        self.detector.close()
        if self.hud:
            self.hud.close()
