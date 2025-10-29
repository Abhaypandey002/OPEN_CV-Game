import json

from src.voice.listener import VoiceListener
from src.core.events import VoiceCommand


class DummyCfg:
    def __init__(self):
        self.voice = {"enabled": True, "model_path": "./fake"}


def test_handle_voice_result(monkeypatch):
    emitted = []

    listener = VoiceListener(DummyCfg(), callback=emitted.append)

    def fake_callback(cmd: VoiceCommand):
        emitted.append(cmd)

    listener.callback = fake_callback
    listener._recognizer = object()
    listener._model = object()

    payload = json.dumps({"text": "start game", "confidence": 0.85})
    listener._handle_result(payload)

    assert emitted
    assert emitted[0].command == "start game"
