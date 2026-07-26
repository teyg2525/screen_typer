"""Text recognition on a captured screen frame via Windows.Media.Ocr."""

import asyncio

from winrt.windows.globalization import Language
from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.security.cryptography import CryptographicBuffer
from winrt.windows.storage.streams import Buffer

from screen_typer.text_observation import TextObservation

_OCR_LANGUAGE = Language("en-US")


def _bgra_frame_to_software_bitmap(frame) -> SoftwareBitmap:
    width, height = frame.width, frame.height
    raw_bytes = bytes(frame.raw)  # mss gives BGRA already, which SoftwareBitmap expects

    buffer = Buffer(len(raw_bytes))
    CryptographicBuffer.copy_bytes_to_buffer_bytearray_wrapper(bytearray(raw_bytes), buffer)
    buffer.length = len(raw_bytes)

    return SoftwareBitmap.create_copy_from_buffer(
        buffer, BitmapPixelFormat.BGRA8, width, height
    )


async def _recognize_async(frame) -> list[TextObservation]:
    if not OcrEngine.is_language_supported(_OCR_LANGUAGE):
        engine = OcrEngine.try_create_from_user_profile_languages()
    else:
        engine = OcrEngine.try_create_from_language(_OCR_LANGUAGE)

    if engine is None:
        return []

    bitmap = _bgra_frame_to_software_bitmap(frame)
    result = await engine.recognize_async(bitmap)

    width, height = frame.width, frame.height
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
