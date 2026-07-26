"""Core loop: capture the region, OCR it, type any newly-seen words."""

import platform
import threading
import time

from screen_typer.dedup import DedupTracker

if platform.system() == "Windows":
    from screen_typer.platform_windows.capture import RegionCapture
    from screen_typer.platform_windows.color_filter import is_bright_text
    from screen_typer.platform_windows.keystrokes import type_text
    from screen_typer.platform_windows.ocr import recognize_text
else:
    from screen_typer.platform_macos.capture import RegionCapture
    from screen_typer.platform_macos.keystrokes import type_text
    from screen_typer.platform_macos.ocr import recognize_text

    def is_bright_text(frame, bounding_box: tuple[float, float, float, float]) -> bool:
        return True

POLL_INTERVAL_SECONDS = 0.08  # ~12 fps
DEDUP_TTL_SECONDS = 5.0


class WatchLoop:
    def __init__(self, region: tuple[float, float, float, float]):
        self._capture = RegionCapture(region)
        self._dedup = DedupTracker(ttl_seconds=DEDUP_TTL_SECONDS)
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._letters_only = False
        self._bright_only = False

    def start(self) -> None:
        if not self._running.is_set():
            self._running.set()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._running.clear()

    def toggle(self) -> None:
        if self._running.is_set():
            self.stop()
        else:
            self.start()

    def set_region(self, region: tuple[float, float, float, float]) -> None:
        self._capture = RegionCapture(region)

    def toggle_letters_only(self) -> None:
        self._letters_only = not self._letters_only

    @property
    def letters_only(self) -> bool:
        return self._letters_only

    def toggle_bright_only(self) -> None:
        self._bright_only = not self._bright_only

    @property
    def bright_only(self) -> bool:
        return self._bright_only

    def set_dedup_ttl(self, ttl_seconds: float) -> None:
        self._dedup.set_ttl_seconds(ttl_seconds)

    @property
    def dedup_ttl(self) -> float:
        return self._dedup.ttl_seconds

    @property
    def is_running(self) -> bool:
        return self._running.is_set()

    def _run(self) -> None:
        while self._running.is_set():
            cycle_start = time.monotonic()

            try:
                frame = self._capture.capture_frame()
                observations = recognize_text(frame)
            except Exception:
                observations = []

            self._dedup.sweep()
            for observation in observations:
                if self._bright_only and not is_bright_text(frame, observation.bounding_box):
                    continue
                word = observation.text
                if self._letters_only:
                    word = "".join(char for char in word if char.isalpha())
                if not word:
                    continue
                if self._dedup.should_type(word):
                    self._dedup.mark_typed(word)
                    type_text(word)
                    print(f"Typed: {word!r}")

            elapsed = time.monotonic() - cycle_start
            remaining = POLL_INTERVAL_SECONDS - elapsed
            if remaining > 0:
                time.sleep(remaining)
