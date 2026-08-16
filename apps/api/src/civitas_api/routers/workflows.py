"""Thin HTTP surface for checkpointed incident workflows."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import success_envelope

router = APIRouter(prefix="/api/v1", tags=["workflows"])


class ClarificationRequest(BaseModel):
    answers: dict[str, str] = Field(min_length=1)


class EditableWorkOrder(BaseModel):
    summary: str | None = Field(default=None, min_length=1, max_length=2000)
    required_actions: list[str] | None = None
    suggested_resources: list[str] | None = None
    safety_notes: list[str] | None = None

    model_config = {"extra": "forbid"}


class RoutingOverride(BaseModel):
    primary_department: str = Field(min_length=1, max_length=100)
    secondary_departments: list[str] = Field(default_factory=list, max_length=10)
    escalation_required: bool = False
    rationale: list[str] = Field(default_factory=list, max_length=20)
    policy_references: list[str] = Field(default_factory=list, max_length=50)

    model_config = {"extra": "forbid"}


class ReviewRequest(BaseModel):
    action: Literal["approve", "edit", "reroute", "reject", "request_more_evidence"]
    notes: str | None = Field(default=None, max_length=1000)
    routing: RoutingOverride | None = None
    operational_plan: EditableWorkOrder | None = None

    model_config = {"extra": "forbid"}


def _runtime():
    from civitas_api.main import app

    runtime = getattr(app.state, "workflow_runtime", None)
    if runtime is None:
        raise HTTPException(status_code=503, detail="workflow runtime is not configured")
    return runtime


def _call(fn, *args):
    try:
        return success_envelope(fn(*args))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/reports/{report_id}/workflow")
def start(
    report_id: str, _: Annotated[Principal, Depends(require_role(Role.CITIZEN))]
) -> dict[str, Any]:
    return _call(_runtime().start, report_id)


@router.get("/workflows/{workflow_id}")
def get(
    workflow_id: str, _: Annotated[Principal, Depends(require_role(Role.CITIZEN))]
) -> dict[str, Any]:
    return _call(_runtime().get, workflow_id)


@router.post("/workflows/{workflow_id}/clarification")
def clarification(
    workflow_id: str,
    body: ClarificationRequest,
    _: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
) -> dict[str, Any]:
    return _call(_runtime().clarification, workflow_id, body.answers)


@router.post("/workflows/{workflow_id}/review")
def review(
    workflow_id: str,
    body: ReviewRequest,
    _: Annotated[Principal, Depends(require_role(Role.REVIEWER))],
) -> dict[str, Any]:
    return _call(_runtime().review, workflow_id, body.model_dump(exclude_none=True))
