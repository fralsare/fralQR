#!/usr/bin/env python3
"""Generate fralQR app icons: packaging/icon.png (256x256) and packaging/icon.ico.

Dev utility. The generated files are committed to the repo, so CI uses them
directly (it only regenerates these if they are missing).

    python packaging/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
BG = (11, 87, 208, 255)    # #0B57D0
FG = (255, 255, 255, 255)  # white


def draw_icon(size):
    s = size / 256.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(56 * s), fill=BG)

    u = max(1, int(10 * s))

    def rect(x, y, w, h, fill):
        d.rectangle([x, y, x + w, y + h], fill=fill)

    def finder(ox, oy):
        rect(ox, oy, 7 * u, 7 * u, FG)
        rect(ox + u, oy + u, 5 * u, 5 * u, BG)
        rect(ox + 2 * u, oy + 2 * u, 3 * u, 3 * u, FG)

    base = int(44 * s)
    off = int(100 * s)
    finder(base, base)              # top-left
    finder(base + off, base)        # top-right
    finder(base, base + off)        # bottom-left

    cells = [(0, 0), (2, 0), (3, 1), (1, 2), (3, 2),
             (0, 3), (2, 3), (3, 3), (1, 4), (4, 4), (0, 5)]
    for c, r in cells:
        rect(base + off + c * u, base + off + r * u, u, u, FG)
    return img


def main():
    out = Path(__file__).parent
    img = draw_icon(SIZE)
    img.save(out / "icon.png")
    img.save(out / "icon.ico",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                    (64, 64), (128, 128), (256, 256)])
    print("wrote", out / "icon.png", "and", out / "icon.ico")


if __name__ == "__main__":
    main()
