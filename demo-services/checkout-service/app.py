from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from db import process_checkout_transaction, pool

app = FastAPI(title="Checkout Service", version="1.0.0")

class CheckoutRequest(BaseModel):
    order_id: str
    amount: float
    trigger_failure: bool = False

@app.get("/health")
async def health():
    return {
        "status": "healthy" if pool.active_connections_count < pool.max_size else "degraded",
        "active_connections": pool.active_connections_count,
        "max_connections": pool.max_size,
    }

@app.post("/api/v1/checkout/orders")
async def create_checkout_session(request: CheckoutRequest):
    try:
        result = await process_checkout_transaction(
            order_id=request.order_id,
            should_fail=request.trigger_failure
        )
        return result
    except TimeoutError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Checkout processing error: {str(e)}")
