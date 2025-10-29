"""Calibration CLI."""

from __future__ import annotations

import argparse

from .core.config import load_config
from .core.logging_setup import setup_logging
from .ui.wizard import CalibrationWizard


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate gesture sensitivity")
    parser.add_argument("--save", action="store_true", help="Persist calibration to config")
    parser.add_argument("--seconds", type=int, default=10, help="Duration of calibration capture")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config()
    setup_logging()
    wizard = CalibrationWizard(cfg)
    wizard.run(seconds=args.seconds, save=args.save)


if __name__ == "__main__":
    main()
