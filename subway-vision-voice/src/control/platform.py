"""Platform detection helpers for keystroke injection."""

from __future__ import annotations

import platform


def current_platform() -> str:
    system = platform.system().lower()
    if system.startswith("darwin") or system == "macos":
        return "mac"
    if system.startswith("windows"):
        return "windows"
    return "linux"
