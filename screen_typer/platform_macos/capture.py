"""Captures a fixed screen region as a CGImage via ScreenCaptureKit."""

import threading

import ScreenCaptureKit as SCK


class CaptureError(RuntimeError):
    pass


class RegionCapture:
    def __init__(self, region: tuple[float, float, float, float]):
        """region is (x, y, width, height) in screen points, top-left origin."""
        self._region = region
        self._content = self._fetch_shareable_content()
        self._display = self._content.displays()[0]

    @staticmethod
    def _fetch_shareable_content():
        result_holder: dict = {}
        event = threading.Event()

        def handler(content, error):
            result_holder["content"] = content
            result_holder["error"] = error
            event.set()

        SCK.SCShareableContent.getShareableContentWithCompletionHandler_(handler)
        event.wait(timeout=5)

        if result_holder.get("error") is not None or "content" not in result_holder:
            raise CaptureError(f"Failed to fetch shareable content: {result_holder.get('error')}")

        return result_holder["content"]

    def capture_frame(self):
        x, y, width, height = self._region

        content_filter = SCK.SCContentFilter.alloc().initWithDisplay_excludingWindows_(
            self._display, []
        )

        config = SCK.SCStreamConfiguration.alloc().init()
        config.setSourceRect_(((x, y), (width, height)))
        config.setWidth_(int(width))
        config.setHeight_(int(height))
        config.setShowsCursor_(False)

        result_holder: dict = {}
        event = threading.Event()

        def handler(image, error):
            result_holder["image"] = image
            result_holder["error"] = error
            event.set()

        SCK.SCScreenshotManager.captureImageWithFilter_configuration_completionHandler_(
            content_filter, config, handler
        )
        event.wait(timeout=2)

        if result_holder.get("error") is not None or result_holder.get("image") is None:
            raise CaptureError(f"Failed to capture frame: {result_holder.get('error')}")

        return result_holder["image"]
