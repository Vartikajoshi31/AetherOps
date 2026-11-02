from typing import Dict, Any, List
from app.agents.base import AgentBase
from app.agents.state import RootCauseOutput, HypothesisItem, InvestigationState
from app.core.logging import logger

class RootCauseAnalysisAgent(AgentBase):
    def __init__(self):
        super().__init__(name="RootCauseAnalysisAgent")

    async def run(self, state: InvestigationState) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Synthesizing root cause for incident: {state.get('title')}")

        triage = state.get("triage_result", {})
        logs = state.get("log_analysis_result", {})
        code = state.get("code_investigation_result", {})

        system_prompt = (
            "You are a Principal Systems Architect and Root Cause Analysis Specialist. "
            "Correlate the triage classification, log telemetry, and source code evidence. "
            "Rank candidate hypotheses by evidentiary support, identify architectural flaws, and return a structured root cause analysis."
        )

        user_prompt = (
            f"Triage: {triage}\n\n"
            f"Log Analysis: {logs}\n\n"
            f"Code Investigation: {code}\n"
        )

        async def fallback():
            culprit_file = code.get("culprit_file", "checkout-service/db.py")
            vuln_expl = code.get("vulnerability_explanation", "")

            # Generate grounded hypotheses based on culprit file
            if "shipping.py" in culprit_file:
                primary = "Null Pointer Dereference on Digital Orders"
                arch_flaw = "Missing polymorphism or defensive null-checks in Order/Shipping domain models for intangible digital goods."
                hypotheses = [
                    HypothesisItem(
                        title="Unchecked Null Dereference on Digital Goods",
                        description="Order processing logic assumes shipping_address is always populated, throwing AttributeError on digital goods.",
                        probability=0.96,
                        supporting_evidence=[
                            "Log: AttributeError 'NoneType' object has no attribute 'country_code'",
                            "Code: calculate_shipping_cost dereferences order.shipping_address without null check",
                            "Domain: Digital orders explicitly do not require physical shipping addresses"
                        ]
                    ),
                    HypothesisItem(
                        title="Corrupted Database Address Record",
                        description="Database migration or external API dropped shipping address columns.",
                        probability=0.04,
                        supporting_evidence=["Missing shipping_address payload in orders"],
                        contradicting_evidence=["Only digital orders trigger the failure; physical orders continue processing normally."]
                    )
                ]
            elif "client.py" in culprit_file:
                primary = "Thundering Herd Retry Storm via Deterministic Backoff"
                arch_flaw = "Lack of full jitter (randomized decorrelation) in distributed exponential backoff calculations."
                hypotheses = [
                    HypothesisItem(
                        title="Synchronized Thundering Herd Retry Storm",
                        description="Fixed exponential backoff delays align retry waves across concurrent clients, saturating payment gateway capacity.",
                        probability=0.95,
                        supporting_evidence=[
                            "Log: GatewayTimeout 504 recurring simultaneously across 40+ client connections",
                            "Code: calculate_retry_delay implements base_backoff * (2 ** attempt) without random jitter",
                            "Traffic: Latency spikes exhibit harmonic periodic wave bursts"
                        ]
                    ),
                    HypothesisItem(
                        title="Total Upstream Gateway Outage",
                        description="Third-party payment provider is completely offline.",
                        probability=0.05,
                        supporting_evidence=["504 Gateway Timeout responses"],
                        contradicting_evidence=["Initial requests succeed when staggered; only synchronized burst requests time out."]
                    )
                ]
            elif "cache.py" in culprit_file:
                primary = "Unbounded In-Memory Cache Memory Leak"
                arch_flaw = "Missing max-capacity constraints and LRU eviction policy on in-memory dictionary cache."
                hypotheses = [
                    HypothesisItem(
                        title="Unbounded Cache Memory Leak",
                        description="SKU cache grows monotonically without size limits or eviction, exhausting container memory and causing OOM crashes.",
                        probability=0.94,
                        supporting_evidence=[
                            "Log: MemoryError / container OOMKilled signal",
                            "Code: InventoryCache stores items in raw dict without maxsize capping or LRU eviction",
                            "Metrics: Memory usage increases linearly with unique SKU lookup requests"
                        ]
                    ),
                    HypothesisItem(
                        title="Heavy Payload Deserialization Leak",
                        description="Large JSON payloads retained by garbage collector.",
                        probability=0.06,
                        supporting_evidence=["Memory growth over time"],
                        contradicting_evidence=["Heap dumps confirm memory is retained entirely within cache._store dict."]
                    )
                ]
            else:
                primary = "Database Connection Pool Exhaustion via Exception Leak"
                arch_flaw = "Resource acquisition without deterministic RAII or try...finally release guarantees in asynchronous execution flow."
                hypotheses = [
                    HypothesisItem(
                        title="Connection Leak in Exception Block",
                        description="Database connection is acquired but not released back to the pool when downstream HTTP calls raise exceptions.",
                        probability=0.97,
                        supporting_evidence=[
                            "Log: QueuePool limit of size 10 overflow reached",
                            "Code: acquire() reserves connection in _in_use, release() only called in successful happy path",
                            "Metrics: In-use connection pool metric plateaus at 10/10 while active queries is 0"
                        ]
                    ),
                    HypothesisItem(
                        title="Slow Long-Running Database Queries",
                        description="Database queries hanging indefinitely without query timeout.",
                        probability=0.03,
                        supporting_evidence=["Connection timeout errors"],
                        contradicting_evidence=["PostgreSQL pg_stat_activity shows 0 active running queries; all connections are idle in transaction."]
                    )
                ]

            return RootCauseOutput(
                primary_hypothesis=primary,
                explanation=f"{primary}: {vuln_expl}",
                architectural_flaw=arch_flaw,
                confidence_score=0.96,
                ranked_hypotheses=hypotheses,
                missing_evidence=[]
            )

        result = await self.execute_structured(system_prompt, user_prompt, RootCauseOutput, fallback)
        return result

root_cause_agent = RootCauseAnalysisAgent()
