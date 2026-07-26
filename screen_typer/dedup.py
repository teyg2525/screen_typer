"""Tracks recently-typed words so a word falling through several capture
cycles gets typed exactly once instead of once per cycle."""

import time


class DedupTracker:
    def __init__(self, ttl_seconds: float = 5.0):
        self._ttl_seconds = ttl_seconds
        self._last_seen: dict[str, float] = {}

    def set_ttl_seconds(self, ttl_seconds: float) -> None:
        self._ttl_seconds = ttl_seconds

    @property
    def ttl_seconds(self) -> float:
        return self._ttl_seconds

    def should_type(self, word: str) -> bool:
        normalized = word.strip().lower()
        if not normalized:
            result = False
        else:
            now = time.monotonic()
            last_seen = self._last_seen.get(normalized)
            result = last_seen is None or (now - last_seen) > self._ttl_seconds
        return result

    def mark_typed(self, word: str) -> None:
        normalized = word.strip().lower()
        if normalized:
            self._last_seen[normalized] = time.monotonic()

    def sweep(self) -> None:
        now = time.monotonic()
        expired = [w for w, t in self._last_seen.items() if (now - t) > self._ttl_seconds]
        for word in expired:
            del self._last_seen[word]
