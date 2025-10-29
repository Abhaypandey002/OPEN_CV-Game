import time

import pytest

from src.vision.gestures import GestureDetector
from src.core.events import Gesture


@pytest.fixture
def detector():
    cfg = {
        "min_speed": 0.01,
        "cooldown_ms": 10,
        "smoothing_alpha": 0.4,
        "window": 3,
    }
    det = GestureDetector(cfg, use_mediapipe=False)
    return det


def test_classify_velocity_left(detector):
    events = detector.classify_velocity((-0.1, 0.0))
    assert events
    assert events[0].gesture == Gesture.LEFT


def test_classify_velocity_debounce(detector):
    first = detector.classify_velocity((0.1, 0.0))
    assert first
    second = detector.classify_velocity((0.1, 0.0))
    assert second == []
    time.sleep(detector.cooldown_ms / 1000.0)
    third = detector.classify_velocity((0.1, 0.0))
    assert third
