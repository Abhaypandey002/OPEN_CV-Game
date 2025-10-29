"""Calibration wizard for gesture thresholds."""

from __future__ import annotations

import logging
from typing import Dict

from ..vision.pipeline import VisionPipeline

LOGGER = logging.getLogger(__name__)


class CalibrationWizard:
    def __init__(self, cfg) -> None:
        self.cfg = cfg

    def run(self, seconds: int = 10, save: bool = False) -> Dict[str, float]:
        vision = VisionPipeline(self.cfg, event_cb=lambda _: None, hud=None)
        LOGGER.info("Starting calibration for %s seconds", seconds)
        result = vision.calibrate(seconds=seconds)
        LOGGER.info("Calibration result: %s", result)
        if save:
            self.cfg.gesture.update(result)
            self.cfg.save()
            LOGGER.info("Calibration saved to config")
        return result
