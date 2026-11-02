import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.agents.state import InvestigationState
from app.agents.triage import triage_agent
from app.agents.log_analysis import log_analysis_agent
from app.agents.code_investigation import code_investigation_agent
from app.agents.root_cause import root_cause_agent
from app.agents.fix_generation import fix_generation_agent
from app.agents.validation import validation_agent
from app.agents.review import review_agent
from app.core.logging import logger

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ==================== NODE DEFINITIONS ====================

async def triage_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Triage Node for incident {state.get('incident_id')}")
    res = await triage_agent.run(state)
    triage_data = res["data"]

    events = state.get("agent_events", [])
    events.append({
        "agent_name": "TriageAgent",
        "stage": "Triage",
        "message": f"Classified as {triage_data.get('category')} (Priority: {triage_data.get('priority_level')})",
        "timestamp": utc_now_iso()
    })

    return {
        "triage_result": triage_data,
        "current_stage": "Triage Complete",
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + res.get("cost", 0.0)
    }

async def parallel_investigation_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Parallel Log & Code Investigation for incident {state.get('incident_id')}")
    # 1. Log Analysis
    log_res = await log_analysis_agent.run(state)
    log_data = log_res["data"]

    # 2. Code Investigation (incorporates log analysis findings)
    state_with_logs = {**state, "log_analysis_result": log_data}
    code_res = await code_investigation_agent.run(state_with_logs)
    code_data = code_res["data"]

    # Merge evidence items
    all_evidence = state.get("evidence_items", [])
    all_evidence.extend(log_data.get("extracted_evidence", []))
    all_evidence.extend(code_data.get("supporting_evidence", []))

    events = state.get("agent_events", [])
    events.append({
        "agent_name": "LogAnalysisAgent",
        "stage": "Log Analysis",
        "message": f"Detected repeating exception in {log_data.get('culprit_module')}:{log_data.get('culprit_line')}",
        "timestamp": utc_now_iso()
    })
    events.append({
        "agent_name": "CodeInvestigationAgent",
        "stage": "Code Investigation",
        "message": f"Pinpointed vulnerable function {code_data.get('culprit_function')} in {code_data.get('culprit_file')}",
        "timestamp": utc_now_iso()
    })

    return {
        "log_analysis_result": log_data,
        "code_investigation_result": code_data,
        "evidence_items": all_evidence,
        "retrieved_documents": code_res.get("retrieved_chunks", []),
        "current_stage": "Evidence Correlation",
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + log_res.get("tokens", 0) + code_res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + log_res.get("cost", 0.0) + code_res.get("cost", 0.0)
    }

async def root_cause_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Root Cause Synthesis Node for incident {state.get('incident_id')}")
    res = await root_cause_agent.run(state)
    rca_data = res["data"]

    events = state.get("agent_events", [])
    events.append({
        "agent_name": "RootCauseAnalysisAgent",
        "stage": "Root Cause Analysis",
        "message": f"Identified primary root cause: {rca_data.get('primary_hypothesis')} (Confidence: {rca_data.get('confidence_score') * 100:.0f}%)",
        "timestamp": utc_now_iso()
    })

    return {
        "root_cause_analysis": rca_data,
        "hypotheses": rca_data.get("ranked_hypotheses", []),
        "current_stage": "Root Cause Identified",
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + res.get("cost", 0.0)
    }

async def fix_generation_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Fix Generation Node (Attempt #{state.get('retry_count', 0) + 1})")
    res = await fix_generation_agent.run(state)
    fix_data = res["data"]

    events = state.get("agent_events", [])
    events.append({
        "agent_name": "FixGenerationAgent",
        "stage": "Fix Generation",
        "message": f"Synthesized unified diff patch for {fix_data.get('affected_file')} (+{fix_data.get('lines_added')}/-{fix_data.get('lines_removed')})",
        "timestamp": utc_now_iso()
    })

    return {
        "proposed_patch": fix_data,
        "current_stage": "Fix Generated",
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + res.get("cost", 0.0)
    }

async def validation_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Sandboxed Validation Node for incident {state.get('incident_id')}")
    res = await validation_agent.run(state)
    val_data = res["data"]

    events = state.get("agent_events", [])
    status_label = "PASSED" if val_data.get("tests_passed") else "FAILED"
    events.append({
        "agent_name": "ValidationAgent",
        "stage": "Sandbox Validation",
        "message": f"Sandbox execution {status_label}: {val_data.get('summary')}",
        "timestamp": utc_now_iso()
    })

    current_retries = state.get("retry_count", 0)
    next_retries = current_retries if val_data.get("tests_passed") else current_retries + 1

    return {
        "validation_result": val_data,
        "current_stage": "Validation Complete",
        "retry_count": next_retries,
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + res.get("cost", 0.0)
    }

async def review_node(state: InvestigationState) -> Dict[str, Any]:
    logger.info(f"[Orchestrator] Executing Review & Human Sign-off Preparation Node")
    res = await review_agent.run(state)
    review_data = res["data"]

    events = state.get("agent_events", [])
    events.append({
        "agent_name": "ReviewAgent",
        "stage": "Review Gate",
        "message": f"Review complete. Safety verdict: {review_data.get('safety_verdict')}. Awaiting human engineer approval.",
        "timestamp": utc_now_iso()
    })

    return {
        "review_result": review_data,
        "current_stage": "Awaiting Approval",
        "status": "Awaiting Approval",
        "agent_events": events,
        "total_tokens": state.get("total_tokens", 0) + res.get("tokens", 0),
        "total_cost": state.get("total_cost", 0.0) + res.get("cost", 0.0)
    }

# ==================== CONDITIONAL ROUTING ====================

def route_after_validation(state: InvestigationState) -> Literal["review_node", "fix_generation_node"]:
    val = state.get("validation_result", {})
    passed = val.get("tests_passed", False)
    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if passed:
        logger.info(f"[Orchestrator] Validation passed. Routing to review_node.")
        return "review_node"

    if retries < max_retries:
        logger.warning(f"[Orchestrator] Validation failed. Retrying fix generation ({retries}/{max_retries}).")
        return "fix_generation_node"

    logger.warning(f"[Orchestrator] Validation failed and maximum retries ({max_retries}) reached. Routing to review_node with failure flag.")
    return "review_node"

# ==================== LANGGRAPH WORKFLOW BUILDER ====================

def build_investigation_graph():
    workflow = StateGraph(InvestigationState)

    # Add Nodes
    workflow.add_node("triage_node", triage_node)
    workflow.add_node("parallel_investigation_node", parallel_investigation_node)
    workflow.add_node("root_cause_node", root_cause_node)
    workflow.add_node("fix_generation_node", fix_generation_node)
    workflow.add_node("validation_node", validation_node)
    workflow.add_node("review_node", review_node)

    # Add Edges
    workflow.add_edge(START, "triage_node")
    workflow.add_edge("triage_node", "parallel_investigation_node")
    workflow.add_edge("parallel_investigation_node", "root_cause_node")
    workflow.add_edge("root_cause_node", "fix_generation_node")
    workflow.add_edge("fix_generation_node", "validation_node")

    # Conditional Retry Loop
    workflow.add_conditional_edges(
        "validation_node",
        route_after_validation,
        {
            "review_node": "review_node",
            "fix_generation_node": "fix_generation_node"
        }
    )

    workflow.add_edge("review_node", END)

    app = workflow.compile()
    return app

investigation_graph = build_investigation_graph()
