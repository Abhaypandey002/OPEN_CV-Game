"""Download the compact Vosk English model."""

from __future__ import annotations

import argparse
import hashlib
import urllib.request
from pathlib import Path

from rich.progress import Progress

from src.core.config import CONFIG_DIR, DEFAULT_MODEL_DIR

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
MODEL_SHA256 = "7f799a69cdb5828a3c6d53295d85f1e4b74e6a1afd37d399a8ce28b5c8285347"


def download(target: Path, force: bool = False) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    dest = target / "vosk-en.zip"
    model_dir = target / "vosk-en"

    if model_dir.exists() and not force:
        return model_dir

    if dest.exists() and not force:
        if _validate(dest):
            return _extract(dest, model_dir)

    with Progress() as progress:
        task = progress.add_task("Downloading Vosk model", total=None)
        urllib.request.urlretrieve(
            MODEL_URL,
            dest,
            lambda block, block_size, total: progress.update(task, advance=block_size),
        )
        progress.update(task, completed=progress.tasks[task].total or 0)

    if not _validate(dest):
        raise RuntimeError("Checksum mismatch for downloaded model")

    return _extract(dest, model_dir, target)


def _validate(path: Path) -> bool:
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest() == MODEL_SHA256


def _extract(zip_path: Path, target_dir: Path, base_dir: Path) -> Path:
    import zipfile

    if target_dir.exists():
        return target_dir
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(base_dir)
    extracted = next(base_dir.glob("vosk-model-small-en-us-*"))
    extracted.rename(target_dir)
    return target_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Vosk model")
    parser.add_argument("--force", action="store_true", help="Redownload even if present")
    args = parser.parse_args()
    path = download(DEFAULT_MODEL_DIR, force=args.force)
    print(f"Model ready at {path}")


if __name__ == "__main__":
    main()
