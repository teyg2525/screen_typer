"""Classifies a recognized word's on-screen color by sampling pixels inside
its bounding box from the captured BGRA frame."""

GLYPH_MIN = 90  # average-brightness floor to treat a pixel as glyph, not background
BRIGHT_MIN = 190  # max-channel floor to call a glyph pixel "bright" (white/yellow highlight, not deep/mid gray)
BRIGHT_RATIO_MIN = 0.5  # fraction of glyph pixels that must be bright


def _bbox_pixels(frame, bounding_box: tuple[float, float, float, float]):
    x_norm, y_norm, w_norm, h_norm = bounding_box
    width, height = frame.width, frame.height
    raw = frame.raw  # BGRA, row-major, no stride padding

    left = max(0, int(x_norm * width))
    top = max(0, int(y_norm * height))
    right = min(width, left + max(1, int(w_norm * width)))
    bottom = min(height, top + max(1, int(h_norm * height)))

    stride = width * 4
    for y in range(top, bottom):
        row_offset = y * stride
        for x in range(left, right):
            offset = row_offset + x * 4
            b, g, r = raw[offset], raw[offset + 1], raw[offset + 2]
            yield r, g, b


def is_bright_text(frame, bounding_box: tuple[float, float, float, float]) -> bool:
    """A pixel counts as "bright" if its brightest channel (not the average,
    so yellow's zeroed-out blue channel doesn't drag it down) reaches
    BRIGHT_MIN. Returns True if most of the bounding box's glyph pixels
    (brighter than the dark background) qualify as bright."""
    glyph_pixels = [
        (r, g, b) for r, g, b in _bbox_pixels(frame, bounding_box)
        if (r + g + b) / 3 >= GLYPH_MIN
    ]
    if not glyph_pixels:
        return False

    bright_pixels = [(r, g, b) for r, g, b in glyph_pixels if max(r, g, b) >= BRIGHT_MIN]
    return len(bright_pixels) / len(glyph_pixels) >= BRIGHT_RATIO_MIN
