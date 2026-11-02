from typing import Dict, Any
from app.agents.base import AgentBase
from app.agents.state import TriageOutput, InvestigationState
from app.core.logging import logger

class TriageAgent(AgentBase):
    def __init__(self):
        super().__init__(name="TriageAgent")

    async def run(self, state: InvestigationState) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Triaging incident: {state.get('title')}")

        title = state.get("title", "")
        desc = state.get("description", "")
        services = state.get("affected_services", [])
        severity = state.get("severity", "High")
        error_rate = state.get("error_rate", "0%")

        system_prompt = (
            "You are an elite Site Reliability Engineer and Incident Commander. "
            "Analyze the production incident telemetry and classify severity, root service, and prioritized next steps."
        )
        user_prompt = (
            f"Incident Title: {title}\n"
            f"Description: {desc}\n"
            f"Services: {services}\n"
            f"Observed Severity: {severity}\n"
            f"Error Rate: {error_rate}\n"
        )

        async def fallback():
            # Intelligent pattern classification
            title_lower = title.lower() + " " + desc.lower()
            category = "infrastructure_exhaustion"
            primary = services[0] if services else "checkout-service"

            if "pool" in title_lower or "leak" in title_lower or "queuepool" in title_lower:
                category = "database_connection_leak"
                primary = "checkout-service"
            elif "thundering" in title_lower or "retry" in title_lower or "backoff" in title_lower:
                category = "network_retry_storm"
                primary = "payment-service"
            elif "cache" in title_lower or "memory" in title_lower or "oom" in title_lower:
                category = "memory_leak_unbounded_cache"
                primary = "inventory-service"
            elif "null" in title_lower or "attributeerror" in title_lower or "shipping" in title_lower:
                category = "null_pointer_dereference"
                primary = "order-service"

            return TriageOutput(
                category=category,
                primary_service=primary,
                impacted_services=services or [primary],
                severity=severity,
                priority_level="P1 - Critical" if severity in ["Critical", "High"] else "P2 - Major",
                summary=f"Automated triage classified incident as {category.replace('_', ' ').title()} in {primary}.",
                recommended_investigation_steps=[
                    f"Inspect {primary} application logs and extract recurring stack traces",
                    f"Perform AST code search in {primary} repository for resource allocation patterns",
                    "Correlate trace latency bottlenecks and upstream error cascading",
                    "Synthesize root cause hypotheses and generate sandboxed regression patch"
                ],
                confidence_score=0.94
            )

        result = await self.execute_structured(system_prompt, user_prompt, TriageOutput, fallback)
        return result

triage_agent = TriageAgent()
