from typing import Dict, Any
from app.agents.base import AgentBase
from app.agents.state import FixOutput, InvestigationState
from app.core.logging import logger

class FixGenerationAgent(AgentBase):
    def __init__(self):
        super().__init__(name="FixGenerationAgent")

    async def run(self, state: InvestigationState) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Generating minimal code fix for incident: {state.get('title')}")

        code = state.get("code_investigation_result", {})
        rca = state.get("root_cause_analysis", {})
        culprit_file = code.get("culprit_file", "checkout-service/db.py")
        retry_count = state.get("retry_count", 0)

        system_prompt = (
            "You are a Principal Software Engineer and Patch Validation Expert. "
            "Generate a minimal, surgical unified diff patch and a targeted regression test suite. "
            "Never introduce unrelated modifications. Return a valid unified diff format."
        )

        user_prompt = (
            f"Culprit File: {culprit_file}\n"
            f"Root Cause: {rca.get('primary_hypothesis')}\n"
            f"Architectural Flaw: {rca.get('architectural_flaw')}\n"
            f"Previous Retry Attempts: {retry_count}\n"
        )

        async def fallback():
            if "shipping.py" in culprit_file:
                diff = (
                    "--- a/order-service/shipping.py\n"
                    "+++ b/order-service/shipping.py\n"
                    "@@ -10,7 +10,10 @@ def calculate_shipping_cost(order: Order) -> float:\n"
                    "     if order.is_digital:\n"
                    "         return 0.0\n"
                    "     \n"
                    "-    country = order.shipping_address.country_code\n"
                    "+    if not order.shipping_address:\n"
                    "+        return 0.0\n"
                    "+    country = order.shipping_address.country_code\n"
                    "     if country == 'US':\n"
                    "         return 5.99\n"
                )
                test_code = (
                    "from shipping import Order, calculate_shipping_cost\n\n"
                    "def test_digital_order_null_shipping_address():\n"
                    "    order = Order(id='reg-001', is_digital=True, shipping_address=None)\n"
                    "    cost = calculate_shipping_cost(order)\n"
                    "    assert cost == 0.0\n"
                )
                explanation = "Adds defensive null-check for order.shipping_address on digital and intangible orders, returning 0.0 shipping fee safely."
                risk = "Low. Digital orders are explicitly free of physical shipping charges."
                added, removed = 3, 1

            elif "client.py" in culprit_file:
                diff = (
                    "--- a/payment-service/client.py\n"
                    "+++ b/payment-service/client.py\n"
                    "@@ -18,6 +18,8 @@ class PaymentGatewayClient:\n"
                    "     def calculate_retry_delay(self, attempt: int) -> float:\n"
                    "         if self.use_jitter:\n"
                    "-            return self.base_backoff * (2 ** attempt)\n"
                    "+            import random\n"
                    "+            return self.base_backoff * (2 ** attempt) + random.uniform(0.1, 0.5)\n"
                    "         return self.base_backoff * (2 ** attempt)\n"
                )
                test_code = (
                    "from client import PaymentGatewayClient\n\n"
                    "def test_jittered_backoff_decorrelation():\n"
                    "    client = PaymentGatewayClient(base_backoff=1.0, use_jitter=True)\n"
                    "    delays = [client.calculate_retry_delay(2) for _ in range(10)]\n"
                    "    assert len(set(delays)) > 5, 'Retries must be decorrelated with random jitter'\n"
                )
                explanation = "Enables full random jitter in exponential retry backoff calculation to prevent synchronized thundering herd spikes."
                risk = "Low. Decorrelates retry delays within a controlled 100ms-500ms window."
                added, removed = 2, 1

            elif "cache.py" in culprit_file:
                diff = (
                    "--- a/inventory-service/cache.py\n"
                    "+++ b/inventory-service/cache.py\n"
                    "@@ -14,6 +14,8 @@ class InventoryCache:\n"
                    "     def set(self, key: str, value: Any):\n"
                    "+        if len(self._store) >= self.maxsize:\n"
                    "+            self.evict_oldest()\n"
                    "         self._store[key] = value\n"
                )
                test_code = (
                    "from cache import InventoryCache\n\n"
                    "def test_cache_maxsize_enforcement():\n"
                    "    cache = InventoryCache(maxsize=2, ttl_seconds=60)\n"
                    "    cache.set('k1', 'v1')\n"
                    "    cache.set('k2', 'v2')\n"
                    "    cache.set('k3', 'v3')\n"
                    "    assert cache.size <= 2\n"
                )
                explanation = "Enforces maxsize capacity constraint on the in-memory cache, evicting the oldest key when capacity is reached."
                risk = "Low. Protects system memory from unbounded heap growth."
                added, removed = 2, 0

            else:  # checkout-service/db.py
                diff = (
                    "--- a/checkout-service/db.py\n"
                    "+++ b/checkout-service/db.py\n"
                    "@@ -32,7 +32,9 @@ class DatabaseConnectionPool:\n"
                    "     async def acquire(self) -> MockConnection:\n"
                    "         async with self._lock:\n"
                    "             if self._available:\n"
                    "                 conn = self._available.pop(0)\n"
                    "+                conn.in_use = True\n"
                    "                 self._in_use.append(conn)\n"
                    "                 return conn\n"
                    " \n"
                    "     async def release(self, conn: MockConnection):\n"
                    "+        conn.reset_state()\n"
                    "         async with self._lock:\n"
                    "             if conn in self._in_use:\n"
                    "                 self._in_use.remove(conn)\n"
                    "                 self._available.append(conn)\n"
                )
                test_code = (
                    "from db import DatabaseConnectionPool\n\n"
                    "@pytest.mark.asyncio\n"
                    "async def test_connection_release_guarantee():\n"
                    "    pool = DatabaseConnectionPool(max_size=2)\n"
                    "    conn = await pool.acquire()\n"
                    "    await pool.release(conn)\n"
                    "    assert len(pool._available) == 2\n"
                    "    assert len(pool._in_use) == 0\n"
                )
                explanation = "Ensures connections are properly tracked, sanitized, and returned to the available queue upon release."
                risk = "Low. Restores connection pool availability and prevents socket exhaustion."
                added, removed = 2, 0

            return FixOutput(
                affected_file=culprit_file,
                diff=diff,
                explanation=explanation,
                regression_risk=risk,
                test_code=test_code,
                lines_added=added,
                lines_removed=removed
            )

        result = await self.execute_structured(system_prompt, user_prompt, FixOutput, fallback)
        return result

fix_generation_agent = FixGenerationAgent()
