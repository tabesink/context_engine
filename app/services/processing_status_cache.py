from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any


@dataclass
class CachedStatus:
    value: Any
    expires_at: datetime


class ProcessingStatusCache:
    def __init__(self) -> None:
        self._items: dict[str, CachedStatus] = {}
        self._lock = Lock()

    def get(self, key: str):
        now = datetime.now(UTC)
        with self._lock:
            item = self._items.get(key)
            if item is None or item.expires_at <= now:
                return None
            return item.value

    def set(self, key: str, value: Any, *, ttl_seconds: int) -> None:
        with self._lock:
            self._items[key] = CachedStatus(
                value=value,
                expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
            )


processing_status_cache = ProcessingStatusCache()
