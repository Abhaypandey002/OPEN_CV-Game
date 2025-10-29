# Subway Vision Voice

![CI](https://github.com/your-org/subway-vision-voice/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

Vision + voice controller for Subway Surfers (or any endless runner that supports arrow keys).
Control the game with realtime hand gestures captured via webcam and offline voice commands.

https://github.com/your-org/subway-vision-voice/assets/demo.gif

## Highlights

- 🎯 **<120 ms latency** gesture engine powered by MediaPipe Hands with smoothing and debouncing.
- 🗣️ **Offline voice control** via Vosk with grammar-constrained commands for high accuracy.
- 🎮 **Cross-platform keystroke injection** with safe fallbacks for Windows, macOS, and Linux.
- 🛠️ **One-command setup** using `make setup && make run` or pure `pip` commands.
- 🧭 **Calibration wizard & HUD** to tune sensitivity and visualise the pipeline in real time.
- 📊 **Structured logging & metrics hooks** for observability and reproducible demos.
- 🧪 **Unit + integration tests** with GitHub Actions CI across three operating systems.
- 🔒 **Offline-first** with no network access required after the optional voice model download.

## Project Structure

```
subway-vision-voice/
├─ README.md
├─ LICENSE
├─ pyproject.toml
├─ requirements.txt
├─ Makefile
├─ src/
│  ├─ run.py
│  ├─ calibrate.py
│  ├─ core/
│  ├─ vision/
│  ├─ voice/
│  ├─ control/
│  └─ ui/
├─ tests/
├─ scripts/
└─ .github/workflows/ci.yml
```

## Quick Start (All Platforms)

> **Prerequisites**
> - Python 3.10 or 3.11
> - Webcam + microphone access
> - Accessibility permission for keyboard injection (macOS)

### 1. Bootstrap

```bash
python -m venv .venv
source .venv/bin/activate  # PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Or simply:

```bash
make setup
```

### 2. Download the offline voice model

The first run of `src/run.py` prompts for download, or pre-download via:

```bash
python scripts/download_vosk_model.py
```

To stay fully offline, copy a pre-downloaded archive to
`~/.subway_vision/models/vosk-en.zip` and re-run the script with `--force`.

### 3. Run the controller

```bash
python src/run.py
```

or

```bash
make run
```

Use `Ctrl+C` to exit.

### 4. Calibrate (optional but recommended)

```bash
python src/calibrate.py --save
```

This guides you through a 10-second capture to auto-tune gesture thresholds and persist them to `~/.subway_vision/config.yaml`.

## Controls & Gestures

| Gesture        | Action | Key |
|----------------|--------|-----|
| Swipe Left     | Move left lane  | ← |
| Swipe Right    | Move right lane | → |
| Swipe Up       | Jump            | ↑ |
| Swipe Down     | Roll            | ↓ |

Voice commands (offline, grammar constrained):

- `start game`
- `pause game`
- `resume game`
- `quit game` (double confirmation within 2 seconds unless `--unsafe-voice`)

## Configuration

Configuration is stored at `~/.subway_vision/config.yaml` (auto-created). Example defaults:

```yaml
camera:
  index: 0
  resolution: [1280, 720]
  processing_resolution: [640, 360]
gesture:
  min_speed: 0.045
  cooldown_ms: 250
  smoothing_alpha: 0.4
voice:
  enabled: true
  grammar: "start game|pause game|resume game|quit game"
  double_confirm_quit: true
control:
  key_mapping:
    left: left
    right: right
    up: up
    down: down
ui:
  debug_overlay: false
  show_landmarks: false
```

Override any value via CLI flags, e.g.:

```bash
python src/run.py --camera-index 1 --mic-index 2 --debug-overlay --no-voice
```

## Advanced Topics

### Docker

A sealed container build is provided for reproducibility:

```bash
docker compose -f docker/compose.yaml up
```

### Metrics

Enable lightweight local telemetry by setting in `config.yaml`:

```yaml
metrics:
  enabled: true
```

Metrics are written to `~/.subway_vision/metrics.csv`.

### CLI Reference

```
python src/run.py --help
python src/calibrate.py --help
```

Useful flags:

- `--frames N` – process only N frames (used by CI / demos)
- `--no-voice` – disable voice loop
- `--debug-overlay` – enable HUD overlays & gesture traces

### Permissions (macOS)

Grant camera, microphone, and accessibility permissions to Terminal/iTerm (or the app bundle) via **System Settings → Privacy & Security**.

### Troubleshooting

- **High CPU usage** – reduce `camera.processing_resolution` in config.
- **Wrong mic/camera** – pass `--mic-index` / `--camera-index` or edit config.
- **Game ignores input** – ensure accessibility permissions are granted. On Linux, run with `sudo` or set up udev rules for keyboard injection.
- **Voice not working offline** – verify Vosk model download and that `config.yaml` points to the unpacked folder.

## Testing & Quality

```bash
pytest -q
ruff check src tests
mypy src
```

Or via convenience targets:

```bash
make lint
make typecheck
make test
```

CI runs the full suite on Ubuntu, Windows, and macOS for Python 3.10 and 3.11 (see badge above).

## Demo Recording

Use the helper script to capture a reproducible HUD overlay:

```bash
bash scripts/demo_recording.sh
```

This runs the controller headlessly for 300 frames and stores the artefacts in `~/.subway_vision/demos/`.

## Security & Privacy

- The app is offline by default (only the optional Vosk model download uses the network).
- No audio or video is persisted unless `--save-audio` / `--save-video` (future work) is enabled.
- Configuration and metrics are stored locally under `~/.subway_vision`.

## FAQ

**Q: Does this work with other games?**  
A: Yes, any title responding to arrow keys (or remapped keys in config) will work.

**Q: Can I remap to WASD?**  
A: Update `control.key_mapping` in `config.yaml` to `w`, `a`, `s`, `d` respectively.

**Q: How do I run fully offline?**  
A: Download the Vosk model once (e.g. on another machine) and copy it to `~/.subway_vision/models/vosk-en`. No runtime network calls occur.

**Q: Is this safe for competitive play?**  
A: The tool simulates keystrokes. Ensure compliance with the game's terms of service before use.

## License

MIT © 2024 Subway Vision Voice contributors.
