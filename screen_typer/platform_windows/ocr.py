"""Text recognition on a captured screen frame via Windows.Media.Ocr."""

import asyncio

from PIL import Image
from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter

from screen_typer.text_observation import TextObservation

_OCR_LANGUAGE = Language("en-US")

# mss captures 1:1 screen pixels, unlike macOS's Retina-density ScreenCaptureKit
# frames; upscaling before OCR gives the recognizer more detail per glyph.
UPSCALE_FACTOR = 2


def _bgra_frame_to_software_bitmap(frame) -> tuple[SoftwareBitmap, int, int]:
    width, height = frame.width, frame.height
    raw_bytes = bytes(frame.raw)  # mss gives BGRA already, which SoftwareBitmap expects

    if UPSCALE_FACTOR != 1:
        image = Image.frombuffer("RGBA", (width, height), raw_bytes, "raw", "BGRA", 0, 1)
        width, height = width * UPSCALE_FACTOR, height * UPSCALE_FACTOR
        image = image.resize((width, height), Image.LANCZOS)
        raw_bytes = image.tobytes("raw", "BGRA")

    writer = DataWriter()
    writer.write_bytes(raw_bytes)
    buffer = writer.detach_buffer()

    bitmap = SoftwareBitmap.create_copy_from_buffer(
        buffer, BitmapPixelFormat.BGRA8, width, height
    )
    return bitmap, width, height


async def _recognize_async(frame) -> list[TextObservation]:
    if not OcrEngine.is_language_supported(_OCR_LANGUAGE):
        engine = OcrEngine.try_create_from_user_profile_languages()
    else:
        engine = OcrEngine.try_create_from_language(_OCR_LANGUAGE)

    if engine is None:
        return []

    bitmap, width, height = _bgra_frame_to_software_bitmap(frame)
    result = await engine.recognize_async(bitmap)

    observations: list[TextObservation] = []
    for line in result.lines:
        for word in line.words:
            rect = word.bounding_rect
            observations.append(
                TextObservation(
                    text=word.text,
                    confidence=1.0,  # Windows.Media.Ocr does not expose per-word confidence
                    bounding_box=(
                        rect.x / width,
                        rect.y / height,
                        rect.width / width,
                        rect.height / height,
                    ),
                )
            )

    return observations


def recognize_text(frame) -> list[TextObservation]:
    return asyncio.run(_recognize_async(frame))
