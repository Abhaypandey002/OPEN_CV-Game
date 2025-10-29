"""Gesture detection using MediaPipe Hands with swipe classification."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
    import mediapipe as mp  # type: ignore
except Exception:  # pragma: no cover - handled gracefully in runtime
    mp = None

import numpy as np

from ..core.events import Gesture, GestureEvent
from ..core.utils import VelocityTracker, direction, magnitude, normalize_coords, within_angle

LOGGER = logging.getLogger(__name__)


@dataclass
class GestureDetector:
    cfg: Dict
    use_mediapipe: bool = True

    def __post_init__(self) -> None:
        self.window = int(self.cfg.get("window", 6))
        self.smoothing_alpha = float(self.cfg.get("smoothing_alpha", 0.4))
        self.min_speed = float(self.cfg.get("min_speed", 0.045))
        self.cooldown_ms = int(self.cfg.get("cooldown_ms", 250))
        self._last_trigger: Dict[Gesture, float] = {g: 0.0 for g in Gesture}
        self.tracker = VelocityTracker(window=self.window, alpha=self.smoothing_alpha)
        self._hand_solution = None
        self._setup_detector()

    def _setup_detector(self) -> None:
        if mp and self.use_mediapipe:
            hands = mp.solutions.hands
            self._hand_solution = hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            LOGGER.info("MediaPipe Hands initialised for gesture detection")
        else:
            LOGGER.warning("MediaPipe not available, fallback mode active")
            self.use_mediapipe = False

    def close(self) -> None:
        if self._hand_solution:
            self._hand_solution.close()

    def process_frame(self, frame_bgr) -> List[GestureEvent]:
        if frame_bgr is None:
            return []
        ts = time.time()
        height, width = frame_bgr.shape[:2]
        events: List[GestureEvent] = []
        index_tip = None

        if self.use_mediapipe and self._hand_solution:
            frame_rgb = frame_bgr[:, :, ::-1]
            results = self._hand_solution.process(frame_rgb)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    lm = hand_landmarks.landmark[8]
                    index_tip = (lm.x * width, lm.y * height)
                    break
        else:
            if cv2 is None:
                LOGGER.debug("OpenCV unavailable for fallback gesture detection")
                return []
            # naive fallback: use centroid of largest contour
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (11, 11), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contour = max(contours, key=cv2.contourArea)
                m = cv2.moments(contour)
                if m["m00"]:
                    index_tip = (m["m10"] / m["m00"], m["m01"] / m["m00"])

        if index_tip is None:
            LOGGER.debug("No fingertip detected this frame")
            return []

        nx, ny = normalize_coords(index_tip[0], index_tip[1], width, height)
        self.tracker.add(ts, nx, ny)
        events.extend(self.classify_velocity(self.tracker.smoothed_velocity()))
        return events

    def calibrate(self, frames: List[np.ndarray]) -> Dict[str, float]:
        """Estimate dynamic gesture parameters from sample frames."""

        speeds = []
        for frame in frames:
            events = self.process_frame(frame)
            if events:
                speeds.extend(event.confidence for event in events)
        if not speeds:
            return {"min_speed": self.min_speed}
        avg_speed = float(np.median(speeds))
        tuned = max(self.min_speed, avg_speed * 0.9)
        return {"min_speed": tuned}

    def classify_velocity(self, velocity: Tuple[float, float]) -> List[GestureEvent]:
        events: List[GestureEvent] = []
        speed = magnitude(velocity)
        if speed < self.min_speed:
            return events
        ang = direction(velocity)
        LOGGER.debug("Velocity %.3f, angle %.2f", speed, ang)
        now = time.time()
        for gesture, target in _GESTURE_ANGLES.items():
            if within_angle(ang, target, 30):
                last_ts = self._last_trigger[gesture]
                if now - last_ts >= self.cooldown_ms / 1000.0:
                    self._last_trigger[gesture] = now
                    confidence = min(1.0, speed / self.min_speed)
                    events.append(GestureEvent(gesture=gesture, confidence=confidence))
        return events


_GESTURE_ANGLES: Dict[Gesture, float] = {
    Gesture.LEFT: 180.0,
    Gesture.RIGHT: 0.0,
    Gesture.UP: -90.0,
    Gesture.DOWN: 90.0,
}

try:
    import cv2  # noqa: E402
except Exception:  # pragma: no cover
    cv2 = None
