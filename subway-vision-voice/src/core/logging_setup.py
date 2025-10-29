"""Logging utilities."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from .config import CONFIG_DIR, DEFAULT_LOG_PATH


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    """Configure logging for the application."""

    log_level = getattr(logging, level.upper(), logging.INFO)
    log_dir = log_file.parent if log_file else DEFAULT_LOG_PATH
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_file or (log_dir / "app.log")

    handlers = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except OSError:
        # If we cannot write logs (e.g. permissions), fallback to console only.
        pass

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(threadName)s | %(name)s | %(message)s",
        handlers=handlers,
    )

    os.environ.setdefault("SUBWAY_VISION_LOG", str(log_path))


__all__ = ["setup_logging", "CONFIG_DIR"]
