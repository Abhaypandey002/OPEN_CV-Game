"""Offline voice command listener using Vosk."""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from pathlib import Path
from typing import Callable, Optional

try:  # pragma: no cover
    import sounddevice as sd
except Exception:
    sd = None

try:  # pragma: no cover
    from vosk import KaldiRecognizer, Model
except Exception:
    KaldiRecognizer = None
    Model = None

from ..core.events import VoiceCommand
from ..core.config import CONFIG_DIR

LOGGER = logging.getLogger(__name__)

GRAMMAR_PATH = Path(__file__).with_name("grammar.json")


def _load_commands() -> list[str]:
    if GRAMMAR_PATH.exists():
        with GRAMMAR_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data.get("expressions", {}).get("command", []) or []
    return ["start game", "pause game", "resume game", "quit game"]


COMMANDS = _load_commands()


class VoiceListener:
    """Listens to microphone input and emits recognised commands."""

    def __init__(self, cfg, callback: Callable[[VoiceCommand], None]) -> None:
        self.cfg = cfg
        self.callback = callback
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._queue: "queue.Queue[bytes]" = queue.Queue(maxsize=10)
        self._recognizer = None
        self._model = None
        self._mic_stream = None

    def start(self) -> None:
        if self.cfg.voice.get("enabled", True) is False:
            LOGGER.info("Voice control disabled in config")
            return
        if self._thread and self._thread.is_alive():
            return
        if KaldiRecognizer is None or Model is None or sd is None:
            LOGGER.warning("Voice dependencies missing; voice control disabled")
            return
        model_path = Path(self.cfg.voice.get("model_path", CONFIG_DIR / "models" / "vosk-en"))
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at {model_path}. Run scripts/download_vosk_model.py"
            )
        self._model = Model(str(model_path))
        grammar = json.dumps(COMMANDS)
        self._recognizer = KaldiRecognizer(self._model, 16000, grammar)
        mic_index = self.cfg.voice.get("mic_index")
        self._mic_stream = sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
            device=mic_index,
        )
        self._mic_stream.start()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="VoiceLoop", daemon=True)
        self._thread.start()
        LOGGER.info("Voice listener started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._mic_stream:
            self._mic_stream.close()
            self._mic_stream = None
        self._recognizer = None
        self._model = None

    def _audio_callback(self, indata, frames, time_info, status):  # pragma: no cover
        if status:
            LOGGER.warning("Sounddevice status: %s", status)
        try:
            self._queue.put_nowait(bytes(indata))
        except queue.Full:
            LOGGER.warning("Audio queue full, dropping audio chunk")

    def _loop(self) -> None:
        assert self._recognizer is not None
        while not self._stop.is_set():
            try:
                data = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if self._recognizer.AcceptWaveform(data):
                result = self._recognizer.Result()
                self._handle_result(result)
            else:
                partial = self._recognizer.PartialResult()
                LOGGER.debug("Voice partial: %s", partial)

    def _handle_result(self, result: str) -> None:
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            LOGGER.error("Failed to decode Vosk result: %s", result)
            return
        text = parsed.get("text", "").strip()
        if text in COMMANDS:
            confidence = float(parsed.get("confidence", 0.0) or 0.9)
            cmd = VoiceCommand(command=text, confidence=confidence)
            LOGGER.info("Voice recognised: %s (%.2f)", text, confidence)
            self.callback(cmd)


__all__ = ["VoiceListener"]
