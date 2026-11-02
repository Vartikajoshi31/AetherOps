import os
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

class AgentBase:
    """
    Base execution engine for specialized autonomous agents.
    Supports OpenAI structured outputs with fallback to deterministic expert reasoning.
    Tracks token usage and estimated USD cost.
    """

    def __init__(self, name: str):
        self.name = name
        self.api_key = settings.OPENAI_API_KEY
        self.model = getattr(settings, "OPENAI_MODEL", getattr(settings, "DEFAULT_LLM_MODEL", "gpt-4o"))
        self._openai_client = None

        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client for {name}: {e}")

    async def execute_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        fallback_fn
    ) -> Dict[str, Any]:
        """
        Executes structured generation using OpenAI or falls back to intelligent heuristic reasoning.
        Returns a dict containing the parsed schema data + usage metrics.
        """
        if self._openai_client and self.api_key:
            try:
                logger.info(f"[{self.name}] Calling OpenAI ({self.model}) with structured schema {response_model.__name__}...")
                response = await self._openai_client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=response_model,
                    temperature=0.1
                )
                parsed = response.choices[0].message.parsed
                usage = response.usage

                input_tokens = usage.prompt_tokens if usage else 250
                output_tokens = usage.completion_tokens if usage else 150
                cost = (input_tokens * 0.000005) + (output_tokens * 0.000015)

                return {
                    "data": parsed.model_dump(),
                    "tokens": input_tokens + output_tokens,
                    "cost": round(cost, 6),
                    "execution_mode": "openai_llm"
                }
            except Exception as e:
                logger.warning(f"[{self.name}] OpenAI call failed or rate-limited ({e}). Executing expert fallback engine.")

        # Fallback Heuristics Execution
        data = await fallback_fn() if callable(fallback_fn) else fallback_fn
        if isinstance(data, BaseModel):
            data = data.model_dump()

        # Simulated token consumption for offline telemetry tracking
        approx_tokens = (len(system_prompt) + len(user_prompt) + len(json.dumps(data))) // 4
        approx_cost = round((approx_tokens * 0.000005), 6)

        return {
            "data": data,
            "tokens": approx_tokens,
            "cost": approx_cost,
            "execution_mode": "expert_heuristics"
        }
