import threading
import time
from typing import Optional

from flask import request


class RecentViews:
    """Remembers who viewed what recently, so refreshing a page (or scripting the view endpoint)
    doesn't inflate a release's or team's view count. A viewer is their user id when signed in,
    else their client IP.

    Kept in memory per worker process, like the blueprint caches: a restart or a second worker can
    let a repeat view through, which is fine for a popularity tie-breaker.
    """

    _WINDOW_SECONDS = 6 * 60 * 60
    # Expired entries are swept once the map grows past this, so it can't grow without bound
    _SWEEP_AT = 10_000

    def __init__(self) -> None:
        self._seen: dict[tuple[str, str], float] = {}
        self._lock = threading.Lock()

    def is_new(self, item_id: str, user_id: Optional[str]) -> bool:
        """Whether this view should count, recording it if so."""
        key = (item_id, user_id or f"ip:{self._client_ip()}")
        now = time.monotonic()
        with self._lock:
            if self._seen.get(key, 0) > now:
                return False
            if len(self._seen) >= self._SWEEP_AT:
                self._seen = {k: expires for k, expires in self._seen.items() if expires > now}
            self._seen[key] = now + self._WINDOW_SECONDS
            return True

    @staticmethod
    def _client_ip() -> str:
        # Heroku's router puts the real client first in X-Forwarded-For
        forwarded = request.headers.get('X-Forwarded-For', '')
        return forwarded.split(',')[0].strip() or request.remote_addr or 'unknown'
