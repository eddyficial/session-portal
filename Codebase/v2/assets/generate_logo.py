"""Generate Session Portal v2 logo assets (PNG + ICO) from the same geometry
as ``logo.svg``. Run with ``py -3 Codebase/v2/assets/generate_logo.py``.

Re-runnable and dependency-light (Pillow only) so the raster assets can be
regenerated if the SVG changes.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent

# App palette (mirror of Codebase/v2/config.py)
DEEP = "#0c0c14"
TILE0 = (19, 19, 31, 255)   # gradient top
TILE1 = (8, 8, 15, 255)     # gradient bottom
STROKE = (27, 27, 43, 255)
BLUE = (159, 197, 255, 255)
GREEN = (184, 247, 179, 255)
PURPLE = (216, 180, 255, 255)
PINK = (255, 122, 217, 255)


def _gradient(size: int, top, bottom) -> Image.Image:
    img = Image.new("RGBA", (size, size), DEEP)
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(size):
            px[x, y] = (r, g, b, 255)
    return img


def _arch_path(d: ImageDraw.ImageDraw, scale: float):
    """Draw the portal doorway + opening + play triangle at ``scale``."""
    s = scale
    # arched frame (blue): rounded-top doorway, square bottom, open at the floor.
    # Built as: filled rounded rectangle for the arch, plus a rect to square the
    # bottom, then punch the opening in the deep tile color.
    d.rounded_rectangle([74 * s, 58 * s, 182 * s, 210 * s],
                        radius=int(54 * s), fill=BLUE)
    d.rectangle([74 * s, 116 * s, 182 * s, 210 * s], fill=BLUE)
    # opening (punch)
    d.rounded_rectangle([96 * s, 80 * s, 160 * s, 210 * s],
                        radius=int(32 * s), fill=DEEP)
    d.rectangle([96 * s, 116 * s, 160 * s, 210 * s], fill=DEEP)
    # resume-play triangle
    d.polygon([(116 * s, 104 * s), (116 * s, 156 * s), (154 * s, 130 * s)], fill=GREEN)


def render(size: int = 256) -> Image.Image:
    img = _gradient(size, TILE0, TILE1)
    d = ImageDraw.Draw(img)
    scale = size / 256.0
    # tile border
    d.rounded_rectangle([8 * scale, 8 * scale, 248 * scale, 248 * scale],
                        radius=int(56 * scale), outline=STROKE,
                        width=max(1, int(2 * scale)))
    # keystone dots (only when large enough to read)
    if size >= 64:
        r = max(2, int(5 * scale))
        d.ellipse([112 * scale - r, 46 * scale - r, 112 * scale + r, 46 * scale + r], fill=PURPLE)
        d.ellipse([128 * scale - r, 42 * scale - r, 128 * scale + r, 42 * scale + r], fill=BLUE)
        d.ellipse([144 * scale - r, 46 * scale - r, 144 * scale + r, 46 * scale + r], fill=PINK)
    _arch_path(d, scale)
    return img


def main() -> None:
    big = render(256)
    big.save(ASSETS / "logo_256.png")
    big.resize((64, 64), Image.LANCZOS).save(ASSETS / "logo_64.png")
    big.resize((32, 32), Image.LANCZOS).save(ASSETS / "logo_32.png")
    # Multi-size ICO for window taskbar icon + desktop shortcut.
    big.save(ASSETS / "logo.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("wrote:", "logo_256.png", "logo_64.png", "logo_32.png", "logo.ico")


if __name__ == "__main__":
    main()