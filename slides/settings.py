"""Church name, language, and theme remembered on this PC."""

from __future__ import annotations

import json
import os
from pathlib import Path


def settings_path() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    folder = root / "WordOnAirLabs" / "WordOnAirSlides"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "settings.json"


def load_settings() -> dict:
    path = settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(data: dict) -> None:
    settings_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
