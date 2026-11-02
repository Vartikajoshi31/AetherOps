import pytest
from shipping import Order, ShippingAddress, calculate_shipping_cost

def test_physical_order_shipping():
    order = Order(
        id="ord-001",
        is_digital=False,
        shipping_address=ShippingAddress(country_code="US", city="Seattle", postal_code="98101")
    )
    assert calculate_shipping_cost(order) == 5.99

def test_digital_order_no_shipping_address():
    order = Order(
        id="ord-002",
        is_digital=True,
        shipping_address=None
    )
    # Must NOT raise AttributeError / NullPointer
    cost = calculate_shipping_cost(order)
    assert cost == 0.0
