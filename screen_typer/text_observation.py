"""Shared OCR result type, returned by both platform OCR backends."""

from dataclasses import dataclass


@dataclass
class TextObservation:
    text: str
    confidence: float
    bounding_box: tuple[float, float, float, float]  # normalized x, y, w, h
