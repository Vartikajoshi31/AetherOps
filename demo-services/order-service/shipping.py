from typing import Optional
from pydantic import BaseModel

class ShippingAddress(BaseModel):
    country_code: str
    city: str
    postal_code: str

class Order(BaseModel):
    id: str
    is_digital: bool = False
    shipping_address: Optional[ShippingAddress] = None

COUNTRY_RATES = {
    "US": 5.99,
    "CA": 8.99,
    "GB": 7.50,
    "DE": 6.50,
}

def calculate_shipping_cost(order: Order) -> float:
    # Safe defensive check for digital items and missing addresses
    if order.is_digital or order.shipping_address is None:
        return 0.0

    country = order.shipping_address.country_code.upper()
    return COUNTRY_RATES.get(country, 15.00)
