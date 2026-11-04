"""Download Noto Nastaliq Urdu (SIL Open Font License) for Urdu slides."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

DEST_DIR = Path(__file__).resolve().parent / "Fonts"
FONT_NAME = "NotoNastaliqUrdu-Regular.ttf"
ZIP_URL = "https://github.com/notofonts/nastaliq/releases/download/NotoNastaliqUrdu-v4.000/NotoNastaliqUrdu-v4.000.zip"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    font_path = DEST_DIR / FONT_NAME
    if font_path.is_file() and font_path.stat().st_size > 100_000 and (DEST_DIR / "OFL.txt").is_file():
        print(f"Font already present: {font_path}")
        return
    with urlopen(ZIP_URL, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        font_member = next((name for name in names if name.endswith("NotoNastaliqUrdu-Regular.ttf")), None)
        license_member = next((name for name in names if name.endswith("OFL.txt")), None)
        if font_member is None:
            raise SystemExit("The font release did not contain NotoNastaliqUrdu-Regular.ttf")
        font_path.write_bytes(archive.read(font_member))
        if license_member:
            (DEST_DIR / "OFL.txt").write_bytes(archive.read(license_member))
    print(f"Wrote {font_path} ({font_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
