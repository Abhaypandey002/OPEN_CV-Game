"""Cross-platform keystroke injection."""

from __future__ import annotations

import logging
import time
from typing import Callable, Dict

from .platform import current_platform

LOGGER = logging.getLogger(__name__)

try:
    import keyboard  # type: ignore
except Exception:  # pragma: no cover
    keyboard = None

try:  # pragma: no cover
    from pynput.keyboard import Controller, Key

    _pynput = Controller()
except Exception:
    Controller = None
    Key = None
    _pynput = None

_RATE_LIMIT = 0.12
_LAST_SENT = 0.0


def _rate_limit() -> bool:
    global _LAST_SENT
    now = time.time()
    if now - _LAST_SENT < _RATE_LIMIT:
        return False
    _LAST_SENT = now
    return True


def _send_key(name: str) -> None:
    if not _rate_limit():
        return
    platform_name = current_platform()
    if platform_name in {"windows", "linux"} and keyboard:
        try:
            keyboard.press(name)
            keyboard.release(name)
            return
        except RuntimeError as exc:
            LOGGER.error("Keyboard injection failed: %s", exc)
    if _pynput:
        key_obj = _key_lookup(name)
        if key_obj is None:
            LOGGER.error("Unknown key %s for pynput", name)
            return
        _pynput.press(key_obj)
        _pynput.release(key_obj)
    else:
        LOGGER.warning("No keyboard backend available for key %s", name)


def _key_lookup(name: str):  # pragma: no cover - simple mapping
    if Key is None:
        return name
    lookup = {
        "left": Key.left,
        "right": Key.right,
        "up": Key.up,
        "down": Key.down,
        "space": Key.space,
        "enter": Key.enter,
        "esc": Key.esc,
    }
    return lookup.get(name, name)


def send_left() -> None:
    _send_key("left")


def send_right() -> None:
    _send_key("right")


def send_up() -> None:
    _send_key("up")


def send_down() -> None:
    _send_key("down")


def send_space() -> None:
    _send_key("space")


def send_enter() -> None:
    _send_key("enter")


def send_escape() -> None:
    _send_key("esc")


__all__ = [
    "send_left",
    "send_right",
    "send_up",
    "send_down",
    "send_space",
    "send_enter",
    "send_escape",
]
