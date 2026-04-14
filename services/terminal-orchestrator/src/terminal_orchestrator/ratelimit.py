import time
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class SpawnRateLimiter:
    """Simple per-user token bucket used to gate container spawns."""

    def __init__(self, per_minute: int) -> None:
        self._capacity = float(max(per_minute, 1))
        self._refill_per_sec = self._capacity / 60.0
        self._buckets: dict[str, _Bucket] = {}
        self._lock = Lock()

    def try_consume(self, user_id: str) -> bool:
        now = time.monotonic()
        with self._lock:
            bucket = self._buckets.get(user_id)
            if bucket is None:
                bucket = _Bucket(tokens=self._capacity, updated_at=now)
                self._buckets[user_id] = bucket
            elapsed = now - bucket.updated_at
            bucket.tokens = min(self._capacity, bucket.tokens + elapsed * self._refill_per_sec)
            bucket.updated_at = now
            if bucket.tokens >= 1.0:
                bucket.tokens -= 1.0
                return True
            return False
