"""Policy / playbook routes:

    GET /api/v1/policies?category=&department=&kind=
    GET /api/v1/policies/{code}
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import success_envelope
from civitas_api.operations import policies as pol_ops

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


@router.get("")
def list_policies(
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
    category: str | None = Query(None),
    department: str | None = Query(None),
    kind: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    rows = pol_ops.list_policies(
        category=category, department=department, kind=kind, limit=limit
    )
    return success_envelope({"policies": rows, "count": len(rows)})


@router.get("/{code}")
def get_policy(
    code: str,
    _principal: Annotated[Principal, Depends(require_role(Role.TRIAGE))],
) -> dict:
    row = pol_ops.get_policy_by_code(code)
    if row is None:
        raise HTTPException(status_code=404, detail="policy not found")
    return success_envelope(row)