import asyncio
import random
from typing import Dict, Any

class GatewayTimeoutException(Exception):
    pass

class PaymentGatewayClient:
    def __init__(self, base_backoff: float = 0.5, use_jitter: bool = False):
        self.base_backoff = base_backoff
        self.use_jitter = use_jitter

    def calculate_retry_delay(self, attempt: int) -> float:
        backoff = self.base_backoff * (2 ** attempt)
        if self.use_jitter:
            return random.uniform(0.1, backoff)
        return backoff

    async def charge(self, amount: float, customer_id: str, simulate_upstream_timeout: bool = False) -> Dict[str, Any]:
        if simulate_upstream_timeout:
            raise GatewayTimeoutException("Upstream payment partner 504 Gateway Timeout")
        return {"charge_id": f"ch_{customer_id[:6]}", "amount": amount, "status": "succeeded"}
