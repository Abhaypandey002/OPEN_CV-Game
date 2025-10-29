"""HUD overlay for vision feedback."""

from __future__ import annotations

import logging
import time
from typing import Iterable, Optional

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

from ..core.events import GestureEvent

LOGGER = logging.getLogger(__name__)


class HeadsUpDisplay:
    """Minimal HUD overlay using OpenCV windows."""

    def __init__(self, debug: bool = False, show_landmarks: bool = False) -> None:
        self.debug = debug
        self.show_landmarks = show_landmarks
        self._last_gesture: Optional[str] = None
        self._last_ts = time.time()

    def update(self, frame, events: Iterable[GestureEvent]) -> None:
        if cv2 is None:
            return
        overlay = frame.copy()
        for event in events:
            self._last_gesture = event.gesture.value
            self._last_ts = time.time()
        fps_text = f"HUD FPS: {1.0 / max(time.time() - self._last_ts, 1e-3):.1f}"
        gesture_text = f"Gesture: {self._last_gesture or 'none'}"
        cv2.putText(overlay, fps_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(overlay, gesture_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Subway Vision HUD", overlay)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            LOGGER.info("HUD window closed by user")

    def close(self) -> None:
        if cv2 is None:
            return
        cv2.destroyWindow("Subway Vision HUD")
