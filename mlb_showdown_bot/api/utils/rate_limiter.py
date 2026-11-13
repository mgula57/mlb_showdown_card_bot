import threading
import time
from collections import deque


class RateLimiter:
    """Allows each key (e.g. a user id) at most `max_events` actions per `window_seconds`.

    Kept in memory per worker process, like `RecentViews`: a restart or a second worker resets
    it, which is fine for slowing down a spammer rather than hard-capping them.
    """

    # Idle keys are swept once the map grows past this, so it can't grow without bound
    _SWEEP_AT = 10_000

    def __init__(self, max_events: int, window_seconds: float) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        """Whether `key` may act now, recording the action if so."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            if len(self._events) >= self._SWEEP_AT:
                self._events = {k: q for k, q in self._events.items() if q and q[-1] > cutoff}
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_events:
                return False
            events.append(now)
            return True
