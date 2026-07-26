"""Text recognition on a captured screen frame via the Vision framework."""

import Vision
from Quartz import CGImageRef  # noqa: F401  (type reference only)

from screen_typer.text_observation import TextObservation


def recognize_text(cg_image) -> list[TextObservation]:
    results: list[TextObservation] = []

    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelFast)
    request.setUsesLanguageCorrection_(False)

    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, None)
    success, error = handler.performRequests_error_([request], None)

    if success:
        observations = request.results() or []
        for observation in observations:
            candidates = observation.topCandidates_(1)
            if not candidates:
                continue
            top = candidates[0]
            box = observation.boundingBox()
            results.append(
                TextObservation(
                    text=str(top.string()),
                    confidence=float(top.confidence()),
                    bounding_box=(box.origin.x, box.origin.y, box.size.width, box.size.height),
                )
            )

    return results
