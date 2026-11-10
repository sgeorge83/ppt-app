"""Build the Chrome Web Store zip for WordOnAir Slides."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.util import Emu

ROOT = Path(__file__).resolve().parents[1]
CHROME = ROOT / "chrome"
DIST = ROOT / "dist" / "chrome"
DATA = ROOT / "data"
LISTING = ROOT / "store" / "chrome"

ENGINE_FILES = (
    "config.js",
    "normalize.js",
    "parser.js",
    "grouping.js",
    "topics.js",
    "bible.js",
)
ROOT_FILES = (
    "manifest.json",
    "background.js",
    "app.html",
    "app.css",
    "app.js",
    "pptx.js",
    "zip.js",
    "blank.pptx",
)


def prepare_bibles() -> None:
    subprocess.check_call([sys.executable, str(ROOT / "packaging" / "prepare_data.py")])


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def icon(size: int) -> Image.Image:
    brand = ROOT / "packaging" / "brand" / "wordonair-icon.png"
    if brand.is_file():
        return Image.open(brand).convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    image = Image.new("RGBA", (size, size), (21, 34, 56, 255))
    draw = ImageDraw.Draw(image)
    bar = max(2, size // 14)
    top = int(size * 0.70)
    draw.rectangle((int(size * 0.18), top, int(size * 0.82), top + bar), fill=(201, 168, 76, 255))
    draw.text((size / 2, size * 0.38), "W", font=font(max(8, int(size * 0.42)), True), fill=(244, 247, 251, 255), anchor="mm")
    return image


def write_icons(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for size in (16, 48, 128):
        icon(size).save(folder / f"{size}.png")
    listing = icon(128)
    LISTING.mkdir(parents=True, exist_ok=True)
    listing.save(LISTING / "icon-128.png")


def clean_template(path: Path) -> None:
    original = zipfile.ZipFile(path)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as package:
        for info in original.infolist():
            name = info.filename
            if name.startswith("ppt/printerSettings/") or name == "docProps/thumbnail.jpeg":
                continue
            data = original.read(name)
            if name.endswith((".xml", ".rels")):
                text = data.decode("utf-8")
                if name == "ppt/presentation.xml":
                    text = re.sub(
                        r"<p:sldSz\b[^>]*/>",
                        '<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>',
                        text,
                    )
                elif name == "ppt/_rels/presentation.xml.rels":
                    text = re.sub(r"<Relationship\b[^>]*printerSettings[^>]*/>", "", text)
                elif name == "[Content_Types].xml":
                    text = re.sub(r'<Default Extension="bin"[^>]*/>', "", text)
                elif name == "docProps/core.xml":
                    text = text.replace("<dc:title/>", "<dc:title>WordOnAir Slides</dc:title>")
                    text = text.replace("<dc:creator/>", "<dc:creator>WordOnAir Labs</dc:creator>")
                    text = text.replace(
                        "generated using python-pptx",
                        "World English Bible and Urdu Geo Version verses.",
                    )
                elif name == "docProps/app.xml":
                    text = text.replace("On-screen Show (4:3)", "On-screen Show (16:9)")
                data = text.encode("utf-8")
            package.writestr(name, data, compress_type=zipfile.ZIP_STORED)
    path.write_bytes(buffer.getvalue())


def write_blank(path: Path) -> None:
    presentation = Presentation()
    presentation.slide_width = Emu(12192000)
    presentation.slide_height = Emu(6858000)
    layout = next(item for item in presentation.slide_layouts if item.name.lower() == "blank")
    presentation.slides.add_slide(layout)
    path.parent.mkdir(parents=True, exist_ok=True)
    presentation.save(path)
    clean_template(path)


def load_chapter(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    verses = []
    numbers = []
    for item in raw.get("verses", []):
        number = int(item["verse"])
        numbers.append(number)
        verses.append((number, str(item.get("text") or "")))
    counted = int(raw.get("verse_count") or 0)
    return {"n": max([counted, *numbers], default=0), "verses": verses}


def build_bible() -> dict:
    english_books = json.loads((DATA / "english" / "books.json").read_text(encoding="utf-8"))
    urdu_books = json.loads((DATA / "urdu" / "books.json").read_text(encoding="utf-8"))
    english_by_id = {int(book["id"]): book for book in english_books}
    urdu_by_id = {int(book["id"]): book for book in urdu_books}
    books = []
    for book_id in sorted(english_by_id):
        english = english_by_id[book_id]
        urdu = urdu_by_id.get(book_id)
        if urdu is None:
            raise SystemExit(f"The Urdu Bible is missing book {book_id}.")
        chapters = []
        count = int(english["chapter_count"])
        for number in range(1, count + 1):
            english_path = DATA / "english" / "chapters" / str(book_id) / f"{number}.json"
            urdu_path = DATA / "urdu" / "chapters" / str(book_id) / f"{number}.json"
            if not english_path.is_file() or not urdu_path.is_file():
                raise SystemExit(f"Missing chapter file for book {book_id}, chapter {number}.")
            english_chapter = load_chapter(english_path)
            urdu_chapter = load_chapter(urdu_path)
            merged: dict[int, list[str]] = {}
            for verse, text in english_chapter["verses"]:
                merged.setdefault(verse, ["", ""])[0] = text
            for verse, text in urdu_chapter["verses"]:
                merged.setdefault(verse, ["", ""])[1] = text
            verse_count = max([english_chapter["n"], urdu_chapter["n"], *merged.keys()], default=0)
            chapters.append(
                {
                    "n": verse_count,
                    "v": [[verse, pair[0], pair[1]] for verse, pair in sorted(merged.items())],
                }
            )
        books.append(
            {
                "id": book_id,
                "en": str(english["name"]),
                "ur": str(urdu["name"]),
                "chapters": chapters,
            }
        )
        print(f"Packed {english['name']}")
    return {"books": books}


def stage() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for name in ROOT_FILES:
        shutil.copy2(CHROME / name, DIST / name)
    engine = DIST / "engine"
    engine.mkdir()
    for name in ENGINE_FILES:
        shutil.copy2(CHROME / "engine" / name, engine / name)
    write_icons(DIST / "icons")
    write_icons(CHROME / "icons")
    bible_path = DIST / "data" / "bible.json"
    bible_path.parent.mkdir()
    bible_path.write_text(json.dumps(build_bible(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {bible_path} ({bible_path.stat().st_size} bytes)")


def pack() -> Path:
    manifest = json.loads((CHROME / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    destination = ROOT / "dist" / f"WordOnAirSlides_{version}_chrome.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as package:
        for path in DIST.rglob("*"):
            if path.is_file():
                package.write(path, path.relative_to(DIST).as_posix())
    names = zipfile.ZipFile(destination).namelist()
    if "manifest.json" not in names:
        raise SystemExit("manifest.json is not at the root of the Chrome package")
    print(f"Wrote {destination} ({destination.stat().st_size} bytes)")
    return destination


def main() -> None:
    write_blank(CHROME / "blank.pptx")
    prepare_bibles()
    stage()
    pack()


if __name__ == "__main__":
    main()
