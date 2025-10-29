"""Event dataclasses shared across the system."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time


class Gesture(Enum):
    """Enumeration of supported gestures."""

    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


@dataclass(slots=True)
class GestureEvent:
    """Represents a gesture that should be converted into an action."""

    gesture: Gesture
    confidence: float
    ts: float = time.time()


@dataclass(slots=True)
class VoiceCommand:
    """Represents a recognised voice command."""

    command: str  # "start game" | "pause game" | "resume game" | "quit game"
    confidence: float
    ts: float = time.time()


GESTURE_TO_ARROW = {
    Gesture.LEFT: "left",
    Gesture.RIGHT: "right",
    Gesture.UP: "up",
    Gesture.DOWN: "down",
}

VOICE_COMMANDS = {
    "start game",
    "pause game",
    "resume game",
    "quit game",
}
