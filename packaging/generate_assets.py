"""Store logos and the Windows icon for WordOnAir Slides."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "Assets"
LISTING = Path(__file__).resolve().parents[1] / "store" / "listing" / "en-US"

NAVY = (21, 34, 56, 255)
GOLD = (201, 168, 76, 255)
MIST = (244, 247, 251, 255)
TEAL = (94, 196, 207, 255)


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


def mark(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), NAVY)
    draw = ImageDraw.Draw(image)
    pad = max(2, size // 16)
    draw.rectangle((0, size - pad * 2, size, size), fill=GOLD)
    draw.rectangle((0, size - pad * 3, size, size - pad * 2), fill=TEAL)
    letter = font(int(size * 0.52), True)
    draw.text((size / 2, size * 0.42), "W", font=letter, fill=MIST, anchor="mm")
    return image


def save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")
    print(f"Wrote {path}")


def wide() -> None:
    image = Image.new("RGBA", (310, 150), NAVY)
    emblem = mark(96)
    image.alpha_composite(emblem, (24, 27))
    draw = ImageDraw.Draw(image)
    draw.text((136, 40), "WordOnAir", font=font(26, True), fill=MIST)
    draw.text((136, 82), "Slides", font=font(22), fill=GOLD)
    save(image, ASSETS / "Wide310x150Logo.png")


def splash() -> None:
    image = Image.new("RGBA", (620, 300), NAVY)
    image.alpha_composite(mark(140), (240, 48))
    draw = ImageDraw.Draw(image)
    draw.text((310, 220), "WordOnAir Slides", font=font(28, True), fill=MIST, anchor="mm")
    draw.text((310, 260), "WordOnAir Labs", font=font(16), fill=GOLD, anchor="mm")
    save(image, ASSETS / "SplashScreen.png")


def icon_file(source: Image.Image) -> None:
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = [source.resize(size, Image.Resampling.LANCZOS) for size in sizes]
    dest = ASSETS / "app.ico"
    images[-1].save(dest, format="ICO", sizes=sizes)
    print(f"Wrote {dest}")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = mark(512)
    names = {
        44: "Square44x44Logo.png",
        50: "StoreLogo.png",
        71: "Square71x71Logo.png",
        150: "Square150x150Logo.png",
        310: "Square310x310Logo.png",
    }
    for size, name in names.items():
        save(source.resize((size, size), Image.Resampling.LANCZOS), ASSETS / name)
    listing = {
        71: "StoreListing71x71.png",
        150: "StoreListing150x150.png",
        300: "StoreListing300x300.png",
    }
    for size, name in listing.items():
        save(source.resize((size, size), Image.Resampling.LANCZOS), LISTING / name)
    wide()
    splash()
    icon_file(source)


if __name__ == "__main__":
    main()
