import pytest
from cache import InventoryCache

def test_inventory_cache_max_size_eviction():
    cache = InventoryCache(maxsize=3, ttl_seconds=60)
    cache.set("SKU-1", {"qty": 10})
    cache.set("SKU-2", {"qty": 20})
    cache.set("SKU-3", {"qty": 30})
    assert cache.size == 3

    # Add 4th item, oldest item (SKU-1) must be evicted
    cache.set("SKU-4", {"qty": 40})
    assert cache.size == 3
    assert cache.get("SKU-1") is None
    assert cache.get("SKU-4") == {"qty": 40}
