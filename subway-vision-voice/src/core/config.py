"""Configuration loading and management."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml

CONFIG_DIR = Path.home() / ".subway_vision"
CONFIG_PATH = CONFIG_DIR / "config.yaml"
DEFAULT_MODEL_DIR = CONFIG_DIR / "models"
DEFAULT_LOG_PATH = CONFIG_DIR / "logs"


DEFAULT_CONFIG: Dict[str, Any] = {
    "camera": {
        "index": 0,
        "resolution": [1280, 720],
        "processing_resolution": [640, 360],
    },
    "gesture": {
        "min_speed": 0.045,
        "cooldown_ms": 250,
        "smoothing_alpha": 0.4,
    },
    "voice": {
        "enabled": True,
        "grammar": "start game|pause game|resume game|quit game",
        "double_confirm_quit": True,
        "model_path": str(DEFAULT_MODEL_DIR / "vosk-en"),
    },
    "control": {
        "key_mapping": {
            "left": "left",
            "right": "right",
            "up": "up",
            "down": "down",
        },
    },
    "ui": {
        "debug_overlay": False,
        "show_landmarks": False,
    },
    "logging": {
        "level": "INFO",
    },
    "metrics": {
        "enabled": False,
    },
}


@dataclass
class AppConfig:
    """High-level strongly typed configuration wrapper."""

    data: Dict[str, Any] = field(default_factory=lambda: deepcopy(DEFAULT_CONFIG))

    @property
    def camera(self) -> Dict[str, Any]:
        return self.data.setdefault("camera", {})

    @property
    def gesture(self) -> Dict[str, Any]:
        return self.data.setdefault("gesture", {})

    @property
    def voice(self) -> Dict[str, Any]:
        return self.data.setdefault("voice", {})

    @property
    def control(self) -> Dict[str, Any]:
        return self.data.setdefault("control", {})

    @property
    def ui(self) -> Dict[str, Any]:
        return self.data.setdefault("ui", {})

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_PATH.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.data, handle, sort_keys=False)


def load_config(override_path: Path | None = None) -> AppConfig:
    """Load configuration from disk, creating defaults if missing."""

    path = override_path or CONFIG_PATH
    if not path.exists():
        cfg = AppConfig(deepcopy(DEFAULT_CONFIG))
        cfg.save()
        return cfg

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    merged = deepcopy(DEFAULT_CONFIG)
    _deep_update(merged, data)
    return AppConfig(merged)


def _deep_update(target: Dict[str, Any], src: Dict[str, Any]) -> None:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value
