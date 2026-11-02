"""Database connection pool management for checkout-service."""
import asyncio
from typing import Optional, List

class MockConnection:
    def __init__(self, conn_id: int):
        self.conn_id = conn_id
        self.is_closed = False

    async def execute(self, query: str, *args):
        if self.is_closed:
            raise RuntimeError("Cannot execute on closed connection")
        await asyncio.sleep(0.01)
        return {"status": "ok", "query": query}

    async def close(self):
        self.is_closed = True

class DatabaseConnectionPool:
    def __init__(self, max_size: int = 10, timeout: float = 2.0):
        self.max_size = max_size
        self.timeout = timeout
        self._available: List[MockConnection] = [MockConnection(i) for i in range(max_size)]
        self._in_use: List[MockConnection] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> MockConnection:
        start_time = asyncio.get_event_loop().time()
        while True:
            async with self._lock:
                if self._available:
                    conn = self._available.pop(0)
                    self._in_use.append(conn)
                    return conn

            if (asyncio.get_event_loop().time() - start_time) > self.timeout:
                raise TimeoutError(
                    f"QueuePool limit of size {self.max_size} overflow reached, connection timed out, timeout {self.timeout}s"
                )
            await asyncio.sleep(0.05)

    async def release(self, conn: MockConnection):
        async with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._available.append(conn)

    @property
    def active_connections_count(self) -> int:
        return len(self._in_use)

pool = DatabaseConnectionPool(max_size=5, timeout=0.5)

# BUGGY PATTERN (Historical/Pre-patch):
# In process_checkout_transaction(), when payment fails, conn is acquired but NOT released in finally block!
async def process_checkout_transaction(order_id: str, should_fail: bool = False):
    conn = await pool.acquire()
    try:
        if should_fail:
            raise RuntimeError(f"Payment gateway timeout for order {order_id}")
        await conn.execute("INSERT INTO orders (id, status) VALUES ($1, $2)", order_id, "PAID")
    finally:
        # Before fix: this was missing if unhandled exception escaped
        await pool.release(conn)
    return {"order_id": order_id, "status": "CONFIRMED"}
