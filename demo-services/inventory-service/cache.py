import time
from collections import OrderedDict
from typing import Optional, Any

class InventoryCache:
    """Bounded LRU Cache with TTL eviction to prevent memory starvation."""
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 300):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self._store = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        value, timestamp = self._store[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any):
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time())
        if len(self._store) > self.maxsize:
            self._store.popitem(last=False)

    @property
    def size(self) -> int:
        return len(self._store)
