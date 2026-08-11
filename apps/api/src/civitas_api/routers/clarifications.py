"""Clarification routes:

    POST /api/v1/reports/{report_id}/clarifications              (TRIAGE)
    POST /api/v1/reports/{report_id}/clarifications/{qid}/answer (CITIZEN)
    GET  /api/v1/reports/{report_id}/clarifications              (TRIAGE)
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import error_envelope, success_envelope
from civitas_api.operations import clarifications as cla_ops

router = APIRouter(prefix="/api/v1/reports", tags=["clarifications"])


@router.post(
    "/{report_id}/clarifications",
    status_code=status.HTTP_201_CREATED,
)
def ask_clarifications(
    report_id: str,
    payload: dict[str, Any],
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    questions = (payload or {}).get("questions") or []
    if not isinstance(questions, list) or not questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.questions (non-empty list) required",
                "retryable": False,
            },
        )
    for q in questions:
        if not isinstance(q, dict) or not q.get("text"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": "each question requires a non-empty 'text' field",
                    "retryable": False,
                },
            )
    rows = cla_ops.ask_clarifications(report_id, questions, asked_by="triage-agent")
    return success_envelope({
        "incident_id": report_id,
        "clarifications": rows,
        "count": len(rows),
    })


@router.post(
    "/{report_id}/clarifications/{question_id}/answer",
    status_code=status.HTTP_200_OK,
)
def answer_clarification(
    report_id: str,
    question_id: str,
    payload: dict[str, Any],
    principal: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
) -> dict[str, Any]:
    answer = (payload or {}).get("answer")
    if not isinstance(answer, str) or not answer.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "payload.answer (non-empty string) required",
                "retryable": False,
            },
        )
    row = cla_ops.answer_clarification(
        report_id, question_id, answer, answered_by=principal.user_id
    )
    return success_envelope(row)


@router.get("/{report_id}/clarifications")
def list_clarifications(
    report_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict[str, Any]:
    rows = cla_ops.list_clarifications(report_id)
    return success_envelope({
        "incident_id": report_id,
        "clarifications": rows,
        "count": len(rows),
    })