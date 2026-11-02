from typing import Dict, Any
from app.models.evaluation import UsageMetric
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Official pricing per million tokens
MODEL_PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "text-embedding-3-small": {"input": 0.02 / 1_000_000, "output": 0.0},
    "default": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
}

class CostService:
    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        rates = MODEL_PRICING.get(model_name, MODEL_PRICING["default"])
        cost = (prompt_tokens * rates["input"]) + (completion_tokens * rates["output"])
        return round(cost, 6)

    @staticmethod
    async def record_usage(
        session: AsyncSession,
        metric_type: str,
        value: float,
        unit: str = "count",
        incident_id: str = None,
        run_id: str = None,
        metadata: Dict[str, Any] = None
    ):
        usage = UsageMetric(
            id=str(uuid.uuid4()),
            metric_type=metric_type,
            incident_id=incident_id,
            run_id=run_id,
            metric_value=value,
            unit=unit,
            metric_attributes=metadata or {}
        )
        session.add(usage)
        await session.flush()
