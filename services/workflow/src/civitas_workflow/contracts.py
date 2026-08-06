from typing import Any

from pydantic import BaseModel, Field


class WorkflowInput(BaseModel):
    report_id: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class WorkflowResult(BaseModel):
    report_id: str
    status: str = "awaiting_implementation"
    trace_id: str | None = None
