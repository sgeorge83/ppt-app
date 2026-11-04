"""Clone the public Bible repositories into data/ for tests and the Store package."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = {
    "english": "https://github.com/sgeorge83/english-bible-data.git",
    "urdu": "https://github.com/sgeorge83/urdu-bible-data.git",
}


def ensure(name: str, url: str) -> None:
    dest = DATA / name
    if (dest / "books.json").is_file():
        print(f"{name} already present")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "clone", "--depth", "1", url, str(dest)])


def main() -> None:
    for name, url in SOURCES.items():
        ensure(name, url)


if __name__ == "__main__":
    main()
