"""Core routing of gesture and voice events."""

from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Callable, Dict

from .events import GESTURE_TO_ARROW, Gesture, GestureEvent, VoiceCommand
from ..control import keys as control_keys

LOGGER = logging.getLogger(__name__)

_GESTURE_LOCK = Lock()
_LAST_GESTURE_TS: Dict[Gesture, float] = {}
_GESTURE_DEBOUNCE = 0.12  # seconds
_LAST_QUIT_COMMAND_TS: float = 0.0


def reset_state() -> None:
    with _GESTURE_LOCK:
        _LAST_GESTURE_TS.clear()
    global _LAST_QUIT_COMMAND_TS
    _LAST_QUIT_COMMAND_TS = 0.0


def handle_gesture(ev: GestureEvent, cfg) -> None:
    """Convert gestures into keystrokes with debounce."""

    cooldown = cfg.gesture.get("cooldown_ms", 250) / 1000.0
    now = time.time()
    with _GESTURE_LOCK:
        last = _LAST_GESTURE_TS.get(ev.gesture, 0.0)
        if now - last < max(cooldown, _GESTURE_DEBOUNCE):
            LOGGER.debug("Gesture %s debounced", ev.gesture)
            return
        _LAST_GESTURE_TS[ev.gesture] = now

    mapping = cfg.control.get("key_mapping", {})
    key_name = mapping.get(GESTURE_TO_ARROW[ev.gesture], GESTURE_TO_ARROW[ev.gesture])
    LOGGER.info("Gesture %s mapped to key %s", ev.gesture.value, key_name)
    _send_key(key_name)


def handle_voice(cmd: VoiceCommand, cfg) -> None:
    """Handle recognised voice commands."""

    voice_cfg = cfg.voice
    command = cmd.command.lower().strip()
    if command not in {"start game", "pause game", "resume game", "quit game"}:
        LOGGER.debug("Ignoring unknown command: %s", command)
        return

    LOGGER.info("Voice command received: %s (%.2f)", command, cmd.confidence)
    if command == "quit game" and voice_cfg.get("double_confirm_quit", True):
        global _LAST_QUIT_COMMAND_TS
        now = time.time()
        if now - _LAST_QUIT_COMMAND_TS <= 2.0:
            LOGGER.warning("Quit confirmed via voice command")
            _send_key("esc")
        else:
            LOGGER.info("Say 'quit game' again within 2 seconds to confirm")
        _LAST_QUIT_COMMAND_TS = now
        return

    if command == "start game":
        _send_key("enter")
    elif command == "pause game":
        _send_key("space")
    elif command == "resume game":
        _send_key("space")


def _send_key(name: str) -> None:
    send_map: Dict[str, Callable[[], None]] = {
        "left": control_keys.send_left,
        "right": control_keys.send_right,
        "up": control_keys.send_up,
        "down": control_keys.send_down,
        "space": control_keys.send_space,
        "enter": control_keys.send_enter,
        "esc": control_keys.send_escape,
    }
    handler = send_map.get(name)
    if handler:
        handler()
    else:
        LOGGER.error("No handler for key %s", name)
