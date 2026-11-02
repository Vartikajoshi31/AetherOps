import pytest
from client import PaymentGatewayClient

def test_retry_delay_deterministic_vs_jitter():
    deterministic_client = PaymentGatewayClient(base_backoff=1.0, use_jitter=False)
    delays_fixed = [deterministic_client.calculate_retry_delay(2) for _ in range(10)]
    assert len(set(delays_fixed)) == 1, "Deterministic backoff produces identical intervals"

    jitter_client = PaymentGatewayClient(base_backoff=1.0, use_jitter=True)
    delays_jittered = [jitter_client.calculate_retry_delay(2) for _ in range(10)]
    assert len(set(delays_jittered)) > 5, "Jittered backoff must produce randomized decorrelated intervals"
