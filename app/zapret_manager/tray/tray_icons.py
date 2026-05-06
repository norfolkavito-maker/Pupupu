from __future__ import annotations

"""Tray icon generation (optional).

This module must NOT import Pillow at import time.
Icons are generated lazily and cached in-memory.
"""

from typing import Any


_CACHE: dict[str, Any] = {}


def _lazy_import_pil() -> tuple[Any, Any]:
    from PIL import Image, ImageDraw  # type: ignore

    return Image, ImageDraw


def get_icon(level: str):
    """Return a PIL.Image for tray icon level.

    Levels: gray|green|blue|purple|yellow|red
    """
    key = (level or "gray").strip().lower() or "gray"
    if key in _CACHE:
        return _CACHE[key]

    Image, ImageDraw = _lazy_import_pil()

    palette = {
        "gray": (110, 110, 110),
        "green": (0, 170, 80),
        "blue": (30, 120, 255),
        "purple": (150, 80, 220),
        "yellow": (235, 190, 30),
        "red": (220, 50, 50),
    }
    color = palette.get(key, palette["gray"])

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # outer border
    draw.ellipse((6, 6, 58, 58), fill=(40, 40, 40, 255))
    # inner circle
    draw.ellipse((10, 10, 54, 54), fill=(*color, 255))

    _CACHE[key] = img
    return img

