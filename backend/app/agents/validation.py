from typing import Dict, Any
from app.agents.base import AgentBase
from app.agents.state import ValidationOutput, InvestigationState
from app.sandbox.runner import sandbox_runner
from app.core.logging import logger

class ValidationAgent(AgentBase):
    def __init__(self):
        super().__init__(name="ValidationAgent")

    async def run(self, state: InvestigationState) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Running sandboxed patch validation for incident: {state.get('title')}")

        patch_data = state.get("proposed_patch", {})
        diff = patch_data.get("diff", "")
        test_code = patch_data.get("test_code", "")
        affected_file = patch_data.get("affected_file", "checkout-service/db.py")
        services = state.get("affected_services", ["checkout-service"])

        # Determine target service from affected file path
        if "/" in affected_file:
            service_name = affected_file.split("/")[0]
        elif "\\" in affected_file:
            service_name = affected_file.split("\\")[0]
        elif services:
            service_name = services[0]
        else:
            service_name = "checkout-service"

        # Execute in sandboxed isolated environment
        sandbox_res = await sandbox_runner.run_sandboxed_validation(
            service_name=service_name,
            affected_file=affected_file,
            diff_patch=diff,
            regression_test_code=test_code,
            timeout_seconds=20
        )

        output = ValidationOutput(
            syntax_valid=sandbox_res.syntax_valid,
            tests_passed=sandbox_res.success,
            tests_run=sandbox_res.tests_run,
            test_failures=sandbox_res.tests_failed,
            stdout=sandbox_res.stdout,
            stderr=sandbox_res.stderr,
            duration_seconds=sandbox_res.duration_seconds,
            summary=(
                f"Sandboxed validation {('PASSED' if sandbox_res.success else 'FAILED')}: "
                f"{sandbox_res.tests_passed}/{sandbox_res.tests_run} tests succeeded in {sandbox_res.duration_seconds}s."
            )
        )

        return {
            "data": output.model_dump(),
            "tokens": 120,
            "cost": 0.0006,
            "execution_mode": "sandbox_runner"
        }

validation_agent = ValidationAgent()
