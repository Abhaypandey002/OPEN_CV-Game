#!/usr/bin/env bash
set -euo pipefail

python src/run.py --no-voice --frames 300 || true
