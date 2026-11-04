"""Locate the bundled World English Bible and Urdu Geo text."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return repo_root()


def data_root() -> Path:
    override = os.environ.get("WORDONAIR_SLIDES_DATA")
    if override:
        return Path(override)
    beside_app = install_root() / "data"
    if (beside_app / "english" / "books.json").is_file():
        return beside_app
    return repo_root() / "data"


def english_dir() -> Path:
    return data_root() / "english"


def urdu_dir() -> Path:
    return data_root() / "urdu"


def bible_text_ready() -> bool:
    return (english_dir() / "books.json").is_file() and (urdu_dir() / "books.json").is_file()


def font_file() -> Path | None:
    candidates = [
        install_root() / "Fonts" / "NotoNastaliqUrdu-Regular.ttf",
        repo_root() / "packaging" / "Fonts" / "NotoNastaliqUrdu-Regular.ttf",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None
