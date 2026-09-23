import time
from threading import Lock
from typing import Generic, Optional, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    """Thread-safe, size-bounded cache with per-entry expiry.

    Plain `dict` + "TTL checked on read" caches never shrink — expired entries
    just sit there until the process restarts, growing memory without bound.
    This sweeps expired entries on write and evicts the oldest entry once
    `max_size` is reached, so the cache can't grow forever.
    """

    def __init__(self, ttl_seconds: float, max_size: int = 500):
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._store: dict[str, tuple[float, V]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[V]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: V, ttl_seconds: Optional[float] = None) -> None:
        with self._lock:
            self._sweep_expired()
            if key not in self._store and len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k][0])
                del self._store[oldest_key]
            expires_at = time.monotonic() + (ttl_seconds if ttl_seconds is not None else self._ttl_seconds)
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _sweep_expired(self) -> None:
        now = time.monotonic()
        expired_keys = [key for key, (expires_at, _) in self._store.items() if now >= expires_at]
        for key in expired_keys:
            del self._store[key]

    def __len__(self) -> int:
        with self._lock:
            self._sweep_expired()
            return len(self._store)
