"""Utility helpers used across modules."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import mean
from typing import Deque, Iterable, Tuple


def ema(previous: float, new: float, alpha: float) -> float:
    """Exponential moving average."""

    return alpha * new + (1 - alpha) * previous


@dataclass
class VelocityTracker:
    """Track fingertip velocity over a sliding window."""

    window: int
    alpha: float
    history: Deque[Tuple[float, float, float]] = None  # time, x, y

    def __post_init__(self) -> None:
        self.history = deque(maxlen=self.window)

    def add(self, ts: float, x: float, y: float) -> None:
        self.history.append((ts, x, y))

    def velocity(self) -> Tuple[float, float]:
        if len(self.history) < 2:
            return 0.0, 0.0
        (t0, x0, y0) = self.history[0]
        (t1, x1, y1) = self.history[-1]
        dt = max(t1 - t0, 1e-6)
        vx = (x1 - x0) / dt
        vy = (y1 - y0) / dt
        return vx, vy

    def smoothed_velocity(self) -> Tuple[float, float]:
        vx, vy = 0.0, 0.0
        samples = list(self.history)
        if len(samples) < 2:
            return vx, vy
        smoothed = []
        prev_vx, prev_vy = 0.0, 0.0
        prev_ts = samples[0][0]
        for ts, x, y in samples[1:]:
            dt = max(ts - prev_ts, 1e-6)
            cur_vx = (x - samples[0][1]) / dt
            cur_vy = (y - samples[0][2]) / dt
            prev_vx = ema(prev_vx, cur_vx, self.alpha)
            prev_vy = ema(prev_vy, cur_vy, self.alpha)
            smoothed.append((prev_vx, prev_vy))
            prev_ts = ts
        if not smoothed:
            return vx, vy
        vx = mean(v for v, _ in smoothed)
        vy = mean(v for _, v in smoothed)
        return vx, vy


def magnitude(vec: Tuple[float, float]) -> float:
    (vx, vy) = vec
    return (vx ** 2 + vy ** 2) ** 0.5


def direction(vec: Tuple[float, float]) -> float:
    import math

    vx, vy = vec
    return math.degrees(math.atan2(vy, vx))


def within_angle(angle: float, target: float, tolerance: float) -> bool:
    import math

    delta = (angle - target + 180) % 360 - 180
    return math.fabs(delta) <= tolerance


def normalize_coords(x: float, y: float, width: int, height: int) -> Tuple[float, float]:
    return x / max(width, 1), y / max(height, 1)


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)
