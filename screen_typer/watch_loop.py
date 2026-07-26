"""Core loop: capture the region, OCR it, type any newly-seen words."""

import threading
import time

from screen_typer.dedup import DedupTracker
from screen_typer.platform_macos.capture import RegionCapture
from screen_typer.platform_macos.keystrokes import type_text
from screen_typer.platform_macos.ocr import recognize_text

POLL_INTERVAL_SECONDS = 0.08  # ~12 fps
DEDUP_TTL_SECONDS = 5.0


class WatchLoop:
    def __init__(self, region: tuple[float, float, float, float]):
        self._capture = RegionCapture(region)
        self._dedup = DedupTracker(ttl_seconds=DEDUP_TTL_SECONDS)
        self._running = threading.Event()
        self._thread: threading.Thread | None = None

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
                word = observation.text
                if self._dedup.should_type(word):
                    self._dedup.mark_typed(word)
                    type_text(word)

            elapsed = time.monotonic() - cycle_start
            remaining = POLL_INTERVAL_SECONDS - elapsed
            if remaining > 0:
                time.sleep(remaining)
