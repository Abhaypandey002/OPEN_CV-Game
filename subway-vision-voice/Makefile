PYTHON ?= python
PIP ?= $(PYTHON) -m pip
VENV ?= .venv

.PHONY: setup run calibrate lint typecheck test demo download-model

setup:
$(PYTHON) -m venv $(VENV)
$(VENV)/bin/python -m pip install -U pip
$(VENV)/bin/python -m pip install -r requirements.txt
rich --version >/dev/null || $(VENV)/bin/python -m pip install rich

run:
$(PYTHON) src/run.py

calibrate:
$(PYTHON) src/calibrate.py --save

lint:
ruff check src tests
ruff format --check src tests
ruff check .

format:
ruff format src tests

typecheck:
mypy src

test:
pytest -q

demo:
bash scripts/demo_recording.sh

download-model:
$(PYTHON) scripts/download_vosk_model.py --force
