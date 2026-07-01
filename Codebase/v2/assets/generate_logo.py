"""Generate Session Portal logo assets (PNG + ICO).

Run with:
    py -3 Codebase/v2/assets/generate_logo.py

The mark is derived from the Session Portal wordmark direction: a luminous
doorway/portal on a deep app-colored tile. It avoids text so the Windows title
bar, taskbar, and Desktop shortcut stay legible at small sizes.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ASSETS = Path(__file__).resolve().parent

# Session Portal app palette with the logo reference's electric violet/blue.
BG_TOP = (17, 17, 27, 255)
BG_BOTTOM = (7, 8, 16, 255)
TILE_STROKE = (48, 52, 82, 255)
INNER_DARK = (9, 10, 22, 255)
SILVER = (222, 226, 242, 255)
SILVER_DARK = (112, 119, 151, 255)
BLUE = (29, 168, 255, 255)
VIOLET = (155, 66, 255, 255)
CYAN = (67, 221, 255, 255)


def _vertical_gradient(size: int, top, bottom) -> Image.Image:
    img = Image.new("RGBA", (size, size), top)
    px = img.load()
    for y in range(size):
        t = y / max(1, size - 1)
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        for x in range(size):
            px[x, y] = row
    return img


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def _stroke(draw: ImageDraw.ImageDraw, points: list[tuple[float, float]], color, width: int) -> None:
    draw.line(points, fill=color, width=width, joint="curve")


def render(size: int = 256) -> Image.Image:
    scale = size / 256
    img = _vertical_gradient(size, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)

    margin = int(10 * scale)
    radius = int(48 * scale)
    d.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=radius,
        fill=None,
        outline=TILE_STROKE,
        width=max(1, int(2 * scale)),
    )

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle(
        (54 * scale, 46 * scale, 198 * scale, 214 * scale),
        radius=int(54 * scale),
        outline=VIOLET,
        width=int(16 * scale),
    )
    gd.line((72 * scale, 212 * scale, 178 * scale, 212 * scale), fill=BLUE, width=int(16 * scale))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(int(10 * scale))))

    # Outer metallic portal frame.
    frame = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    frame_path = [
        (70 * scale, 212 * scale),
        (70 * scale, 114 * scale),
        (72 * scale, 94 * scale),
        (82 * scale, 72 * scale),
        (104 * scale, 58 * scale),
        (152 * scale, 58 * scale),
        (174 * scale, 72 * scale),
        (186 * scale, 94 * scale),
        (188 * scale, 212 * scale),
    ]
    _stroke(fd, frame_path, SILVER_DARK, int(34 * scale))
    _stroke(fd, frame_path, SILVER, int(25 * scale))
    _stroke(fd, frame_path, VIOLET, int(13 * scale))
    _stroke(fd, frame_path, BLUE, int(7 * scale))
    img.alpha_composite(frame)

    # Dark opening.
    d.rounded_rectangle(
        (96 * scale, 86 * scale, 160 * scale, 214 * scale),
        radius=int(30 * scale),
        fill=INNER_DARK,
    )
    d.rectangle((96 * scale, 126 * scale, 160 * scale, 214 * scale), fill=INNER_DARK)

    # Open door slab, inspired by the reference image.
    door = [
        (146 * scale, 100 * scale),
        (180 * scale, 84 * scale),
        (182 * scale, 204 * scale),
        (146 * scale, 218 * scale),
    ]
    d.polygon(door, fill=(46, 56, 93, 255))
    d.line((146 * scale, 100 * scale, 180 * scale, 84 * scale, 182 * scale, 204 * scale, 146 * scale, 218 * scale, 146 * scale, 100 * scale),
           fill=(187, 197, 229, 255), width=max(1, int(2 * scale)))
    d.rounded_rectangle((168 * scale, 142 * scale, 172 * scale, 159 * scale), radius=max(1, int(2 * scale)), fill=CYAN)

    # Perspective floor tiles: visible only at medium and large sizes.
    if size >= 48:
        floor = [
            (104 * scale, 214 * scale),
            (158 * scale, 214 * scale),
            (190 * scale, 236 * scale),
            (72 * scale, 236 * scale),
        ]
        d.polygon(floor, fill=(18, 42, 91, 255))
        for t in (0.24, 0.48, 0.72):
            x1 = (104 + (158 - 104) * t) * scale
            x2 = (72 + (190 - 72) * t) * scale
            d.line((x1, 214 * scale, x2, 236 * scale), fill=VIOLET, width=max(1, int(2 * scale)))
        for y in (221, 228):
            d.line((84 * scale, y * scale, 178 * scale, y * scale), fill=BLUE, width=max(1, int(2 * scale)))

    # Corner highlight to keep the mark lively without changing the app theme.
    highlight = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.arc((34 * scale, 30 * scale, 222 * scale, 226 * scale), 205, 330, fill=(255, 255, 255, 70), width=max(1, int(2 * scale)))
    img.alpha_composite(highlight)

    return img


def main() -> None:
    big = render(256)
    big.save(ASSETS / "logo_256.png")
    big.resize((64, 64), Image.LANCZOS).save(ASSETS / "logo_64.png")
    big.resize((32, 32), Image.LANCZOS).save(ASSETS / "logo_32.png")
    big.save(
        ASSETS / "logo.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    big.save(
        ASSETS / "session_portal.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("wrote:", "logo_256.png", "logo_64.png", "logo_32.png", "logo.ico", "session_portal.ico")


if __name__ == "__main__":
    main()
