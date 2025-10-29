from unittest import mock

from src.control import keys


def test_rate_limit(monkeypatch):
    calls = []

    def fake_press(name):
        calls.append(name)

    monkeypatch.setattr(keys, "keyboard", mock.Mock(press=fake_press, release=fake_press))
    monkeypatch.setattr(keys, "current_platform", lambda: "linux")
    keys._LAST_SENT = 0
    keys._send_key("left")
    assert calls


def test_pynput_fallback(monkeypatch):
    monkeypatch.setattr(keys, "keyboard", None)

    class FakeController:
        def __init__(self):
            self.sent = []

        def press(self, key):
            self.sent.append(("press", key))

        def release(self, key):
            self.sent.append(("release", key))

    fake_controller = FakeController()
    monkeypatch.setattr(keys, "_pynput", fake_controller)
    monkeypatch.setattr(keys, "Key", mock.Mock(left="<left>"))
    monkeypatch.setattr(keys, "current_platform", lambda: "mac")
    keys._LAST_SENT = 0
    keys._send_key("left")
    assert fake_controller.sent[0][0] == "press"
