"""Captures a fixed screen region as a raw BGRA frame via mss."""

import mss


class CaptureError(RuntimeError):
    pass


class RegionCapture:
    def __init__(self, region: tuple[float, float, float, float]):
        """region is (x, y, width, height) in screen points, top-left origin."""
        x, y, width, height = region
        self._monitor = {
            "left": int(x),
            "top": int(y),
            "width": int(width),
            "height": int(height),
        }

    def capture_frame(self):
        try:
            with mss.mss() as sct:
                shot = sct.grab(self._monitor)
        except Exception as error:
            raise CaptureError(f"Failed to capture frame: {error}") from error

        return shot
