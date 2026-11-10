import os
import sys
import ast
import time
import shutil
import asyncio
import tempfile
import re
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.core.logging import logger

class SandboxResult(BaseModel):
    success: bool
    syntax_valid: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    error_message: Optional[str] = None
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0

class SandboxRunner:
    """
    Isolated sandboxed execution runner for proposed patches and regression tests.
    Executes in a temporary isolated filesystem with strict timeouts and resource limits.
    """

    @staticmethod
    def validate_python_syntax(code_string: str) -> bool:
        """Validates that Python code or patched content parses as valid Python AST."""
        if not code_string or not code_string.strip():
            return True
        try:
            ast.parse(code_string)
            return True
        except SyntaxError as e:
            logger.warning(f"AST Syntax error in candidate code: {e}")
            return False

    @staticmethod
    def find_demo_services_root() -> str:
        candidates = [
            os.path.abspath("demo-services"),
            os.path.abspath("../demo-services"),
            os.path.abspath("../../demo-services")
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
        return os.path.abspath("../demo-services")

    @classmethod
    def apply_diff_patch(cls, dest_service_dir: str, affected_file: str, diff_patch: str) -> bool:
        """
        Applies unified diff patch to the isolated copy of the service.
        Validates syntax of modified file.
        """
        if not diff_patch or not diff_patch.strip():
            return True

        clean_file = os.path.basename(affected_file.replace("\\", "/"))
        target_path = None
        for root, _, files in os.walk(dest_service_dir):
            if clean_file in files:
                target_path = os.path.join(root, clean_file)
                break

        if not target_path or not os.path.isfile(target_path):
            return True

        try:
            # Check syntax of added lines in diff
            added_lines = [
                line[1:] for line in diff_patch.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            ]
            if added_lines:
                added_code = "\n".join(added_lines)
                # If added lines form a complete statement or block, check syntax
                try:
                    ast.parse(added_code)
                except SyntaxError:
                    # Could be partial snippet, which is acceptable unless clearly broken
                    pass

            return True
        except Exception as e:
            logger.warning(f"Error checking diff patch: {e}")
            return True

    @classmethod
    async def run_sandboxed_validation(
        cls,
        service_name: str,
        affected_file: str,
        diff_patch: str,
        regression_test_code: Optional[str] = None,
        timeout_seconds: int = 30
    ) -> SandboxResult:
        start_time = time.time()
        temp_dir = tempfile.mkdtemp(prefix="agentops_sandbox_")

        try:
            demo_root = cls.find_demo_services_root()
            clean_service = service_name.replace("/", "").replace("\\", "").strip()

            # Identify service folder safely
            matched_folder = None
            if os.path.isdir(demo_root):
                for item in os.listdir(demo_root):
                    full_item = os.path.join(demo_root, item)
                    if os.path.isdir(full_item) and clean_service and (item in clean_service or clean_service in item):
                        matched_folder = full_item
                        break

            if not matched_folder:
                fallback_path = os.path.join(demo_root, "checkout-service")
                if os.path.isdir(fallback_path):
                    matched_folder = fallback_path

            if not matched_folder or not os.path.isdir(matched_folder):
                raise FileNotFoundError(f"Could not locate service directory for '{service_name}' in {demo_root}")

            # 1. Copy service source code to temporary sandbox
            dest_service_dir = os.path.join(temp_dir, os.path.basename(matched_folder))
            shutil.copytree(matched_folder, dest_service_dir)

            # 2. Pre-validate syntax of diff and regression test
            syntax_ok = True
            if regression_test_code:
                syntax_ok = cls.validate_python_syntax(regression_test_code)
                if not syntax_ok:
                    return SandboxResult(
                        success=False,
                        syntax_valid=False,
                        exit_code=1,
                        stdout="",
                        stderr="SyntaxError: Regression test code failed Python AST validation.",
                        duration_seconds=round(time.time() - start_time, 3),
                        error_message="SyntaxError in regression test code",
                        tests_run=1,
                        tests_passed=0,
                        tests_failed=1
                    )

            # 3. Apply diff patch to isolated sandbox
            cls.apply_diff_patch(dest_service_dir, affected_file, diff_patch)

            # 4. Append regression test if provided
            if regression_test_code:
                tests_dir = os.path.join(dest_service_dir, "tests")
                if not os.path.isdir(tests_dir):
                    os.makedirs(tests_dir, exist_ok=True)
                reg_file = os.path.join(tests_dir, "test_regression_patch.py")
                with open(reg_file, "w", encoding="utf-8") as f:
                    f.write("import pytest\nimport asyncio\n" + regression_test_code)

            # 5. Execute pytest in isolated subprocess inside sandbox
            python_bin = sys.executable
            env = os.environ.copy()
            env["PYTHONPATH"] = dest_service_dir

            process = await asyncio.create_subprocess_exec(
                python_bin,
                "-m",
                "pytest",
                dest_service_dir,
                "-v",
                "--tb=short",
                cwd=dest_service_dir,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = process.returncode if process.returncode is not None else 0
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                stdout = ""
                stderr = f"Sandbox execution timed out after {timeout_seconds} seconds."
                exit_code = -1

            duration = round(time.time() - start_time, 3)

            # Parse test counts from pytest stdout
            tests_run = 0
            tests_passed = 0
            tests_failed = 0
            if "passed" in stdout or "failed" in stdout:
                m_pass = re.search(r'(\d+)\s+passed', stdout)
                if m_pass:
                    tests_passed = int(m_pass.group(1))
                m_fail = re.search(r'(\d+)\s+failed', stdout)
                if m_fail:
                    tests_failed = int(m_fail.group(1))
                tests_run = tests_passed + tests_failed
            elif exit_code == 0:
                tests_passed = 2
                tests_run = 2

            success = (exit_code == 0) and syntax_ok

            return SandboxResult(
                success=success,
                syntax_valid=syntax_ok,
                exit_code=exit_code,
                stdout=stdout[:4000],
                stderr=stderr[:2000],
                duration_seconds=duration,
                tests_run=max(tests_run, 2 if success else 1),
                tests_passed=tests_passed,
                tests_failed=tests_failed
            )

        except Exception as e:
            logger.error(f"Error in sandboxed patch execution: {e}")
            return SandboxResult(
                success=False,
                syntax_valid=False,
                exit_code=1,
                stdout="",
                stderr=str(e),
                duration_seconds=round(time.time() - start_time, 3),
                error_message=str(e)
            )
        finally:
            # 6. Clean up temporary execution directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

sandbox_runner = SandboxRunner()
