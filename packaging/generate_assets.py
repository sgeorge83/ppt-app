"""Store logos and the Windows icon for WordOnAir Slides.

Square icons use the same WordOnAir mark as Bible Widget.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = Path(__file__).resolve().parent / "Assets"
LISTING = ROOT / "store" / "listing" / "en-US"
SOURCE = Path(__file__).resolve().parent / "brand" / "wordonair-icon.png"

NAVY = (21, 34, 56, 255)
GOLD = (201, 168, 76, 255)
MIST = (244, 247, 251, 255)


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


def load_mark() -> Image.Image:
    if not SOURCE.is_file():
        raise SystemExit(f"WordOnAir icon is missing: {SOURCE}")
    return Image.open(SOURCE).convert("RGBA")


def fitted(source: Image.Image, size: int) -> Image.Image:
    return source.resize((size, size), Image.Resampling.LANCZOS)


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")
    print(f"Wrote {path}")


def wide(source: Image.Image) -> None:
    image = Image.new("RGBA", (310, 150), NAVY)
    emblem = fitted(source, 96)
    image.alpha_composite(emblem, (24, 27))
    draw = ImageDraw.Draw(image)
    draw.text((136, 40), "WordOnAir", font=font(26, True), fill=MIST)
    draw.text((136, 82), "Slides", font=font(22), fill=GOLD)
    save(image, ASSETS / "Wide310x150Logo.png")


def splash(source: Image.Image) -> None:
    image = Image.new("RGBA", (620, 300), NAVY)
    emblem = fitted(source, 140)
    image.alpha_composite(emblem, ((620 - 140) // 2, 36))
    draw = ImageDraw.Draw(image)
    draw.text((310, 210), "WordOnAir Slides", font=font(28, True), fill=MIST, anchor="mm")
    draw.text((310, 252), "WordOnAir Labs", font=font(16), fill=GOLD, anchor="mm")
    save(image, ASSETS / "SplashScreen.png")


def icon_file(source: Image.Image) -> None:
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = [fitted(source, size[0]) for size in sizes]
    dest = ASSETS / "app.ico"
    images[-1].save(dest, format="ICO", sizes=sizes)
    print(f"Wrote {dest}")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = load_mark()
    names = {
        44: "Square44x44Logo.png",
        50: "StoreLogo.png",
        71: "Square71x71Logo.png",
        150: "Square150x150Logo.png",
        310: "Square310x310Logo.png",
    }
    for size, name in names.items():
        save(fitted(source, size), ASSETS / name)
    listing = {
        71: "StoreListing71x71.png",
        150: "StoreListing150x150.png",
        300: "StoreListing300x300.png",
    }
    for size, name in listing.items():
        save(fitted(source, size), LISTING / name)
    wide(source)
    splash(source)
    icon_file(source)


if __name__ == "__main__":
    main()
