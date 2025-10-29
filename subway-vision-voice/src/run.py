"""Main entrypoint for Subway Vision Voice controller."""

from __future__ import annotations

import argparse
import logging
import queue
import signal
import threading
import time
from pathlib import Path

from rich.console import Console

from .core.config import AppConfig, load_config
from .core.events import GestureEvent, VoiceCommand
from .core.logging_setup import setup_logging
from .core.router import handle_gesture, handle_voice, reset_state
from .vision.hud import HeadsUpDisplay
from .vision.pipeline import VisionPipeline
from .voice.listener import VoiceListener

LOGGER = logging.getLogger(__name__)


class EventLoop:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.queue: "queue.Queue[tuple[str, GestureEvent | VoiceCommand | None]]" = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="EventRouter")

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self.queue.put(("stop", None))
        self._thread.join(timeout=2.0)

    def push_gesture(self, event: GestureEvent) -> None:
        self.queue.put(("gesture", event))

    def push_voice(self, command: VoiceCommand) -> None:
        self.queue.put(("voice", command))

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                kind, payload = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if kind == "gesture" and isinstance(payload, GestureEvent):
                handle_gesture(payload, self.cfg)
            elif kind == "voice" and isinstance(payload, VoiceCommand):
                handle_voice(payload, self.cfg)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vision + voice controller")
    parser.add_argument("--config", type=str, help="Path to config.yaml", default=None)
    parser.add_argument("--camera-index", type=int, help="Override camera index")
    parser.add_argument("--mic-index", type=int, help="Override microphone index")
    parser.add_argument("--debug-overlay", action="store_true", help="Enable debug HUD")
    parser.add_argument("--no-voice", action="store_true", help="Disable voice control")
    parser.add_argument("--frames", type=int, default=0, help="Stop after N camera frames (for CI)")
    return parser.parse_args()


def main() -> None:
    console = Console()
    args = parse_args()
    cfg_path = None
    if args.config:
        cfg_path = Path(args.config)
    cfg = load_config(cfg_path)
    if args.camera_index is not None:
        cfg.camera["index"] = args.camera_index
    if args.mic_index is not None:
        cfg.voice["mic_index"] = args.mic_index
    if args.debug_overlay:
        cfg.ui["debug_overlay"] = True
    if args.no_voice:
        cfg.voice["enabled"] = False

    setup_logging(cfg.logging.get("level", "INFO"))
    reset_state()

    hud = HeadsUpDisplay(debug=cfg.ui.get("debug_overlay", False))
    event_loop = EventLoop(cfg)
    event_loop.start()

    vision = VisionPipeline(
        cfg=cfg,
        event_cb=event_loop.push_gesture,
        hud=hud,
        frame_limit=args.frames or None,
    )
    voice = VoiceListener(cfg=cfg, callback=event_loop.push_voice)

    def shutdown(signum=None, frame=None):
        LOGGER.info("Shutting down...")
        vision.stop()
        voice.stop()
        event_loop.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    vision.start()
    voice.start()
    console.print("[bold green]Subway Vision Voice running. Press Ctrl+C to exit.[/bold green]")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    from pathlib import Path

    main()
