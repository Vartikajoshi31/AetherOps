from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict

class PatchValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patch_id: str
    status: str
    syntax_valid: bool
    tests_passed: bool
    total_tests: str
    passed_tests: str
    failed_tests: str
    execution_time_seconds: float
    memory_peak_mb: float
    stdout_output: Optional[str] = None
    stderr_output: Optional[str] = None
    regression_detected: bool
    validation_summary: str
    created_at: str

class PatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    run_id: Optional[str] = None
    title: str
    explanation: str
    diff_content: str
    affected_files: List[str] = []
    regression_tests: Optional[str] = None
    status: str
    github_pr_url: Optional[str] = None
    created_at: str
    validations: List[PatchValidationResponse] = []

class ApprovalRequest(BaseModel):
    action: str  # approved, rejected, modified
    feedback: Optional[str] = None
    create_github_pr: bool = False

class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patch_id: str
    incident_id: str
    reviewer_id: Optional[str] = None
    action: str
    feedback: Optional[str] = None
    created_pr: bool
    github_pr_url: Optional[str] = None
    created_at: str
