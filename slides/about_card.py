"""Draw the About card for the Store listing. No window is required."""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from slides.about import APP_NAME, PURPOSE, PUBLISHER

NAVY = (21, 34, 56, 255)
GOLD = (201, 168, 76, 255)
MIST = (244, 247, 251, 255)
MUTED = (92, 110, 134, 255)
WHITE = (255, 255, 255, 255)
TEAL = (94, 196, 207, 255)
BROWN = (138, 100, 48, 255)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render_about_card(destination: Path, size: tuple[int, int] = (1366, 768)) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", size, MIST)
    draw = ImageDraw.Draw(image)
    card = (48, 36, size[0] - 48, size[1] - 36)
    draw.rounded_rectangle(card, radius=18, fill=WHITE)
    draw.rectangle((48, 36, size[0] - 48, 42), fill=GOLD)
    draw.rectangle((48, 42, size[0] - 48, 46), fill=TEAL)
    draw.text((80, 64), PUBLISHER, font=_font(16, True), fill=BROWN)
    draw.text((78, 92), APP_NAME, font=_font(36, True), fill=NAVY)
    draw.text((80, 146), "English and Urdu verses for PowerPoint", font=_font(18), fill=MUTED)

    y = 188
    body = _font(16)
    for paragraph in PURPOSE.strip().split("\n"):
        if not paragraph.strip():
            y += 8
            continue
        face = _font(18, True) if paragraph.strip() in {"How to use it", "Scripture"} else body
        wrapped = textwrap.wrap(paragraph.strip(), width=100) or [""]
        overflow = False
        for line in wrapped:
            if y > size[1] - 110:
                overflow = True
                break
            draw.text((80, y), line, font=face, fill=NAVY)
            y += 24
        if overflow:
            break
    draw.text((80, size[1] - 72), "wordonair.com  ·  a free resource from WordOnAir Labs", font=_font(16, True), fill=BROWN)
    image.convert("RGB").save(destination, format="PNG")
    return destination


if __name__ == "__main__":
    target = Path("store/listing/en-US/about.png")
    render_about_card(target)
    print(f"Wrote {target}")
