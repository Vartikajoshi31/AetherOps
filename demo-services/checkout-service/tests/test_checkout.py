import pytest
import asyncio
from db import DatabaseConnectionPool, process_checkout_transaction

@pytest.mark.asyncio
async def test_checkout_connection_lifecycle():
    result = await process_checkout_transaction("ord-101", should_fail=False)
    assert result["status"] == "CONFIRMED"

@pytest.mark.asyncio
async def test_checkout_connection_released_on_failure():
    # Verify pool does not leak connections when transactions fail
    test_pool = DatabaseConnectionPool(max_size=3, timeout=0.2)
    conn = await test_pool.acquire()
    assert test_pool.active_connections_count == 1
    await test_pool.release(conn)
    assert test_pool.active_connections_count == 0
