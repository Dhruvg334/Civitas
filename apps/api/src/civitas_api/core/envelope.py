"""Common success/error envelope for the Civitas API (ref/04 §2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel

T = TypeVar("T")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _trace_id() -> str:
    return str(uuid4())


def success_envelope(data: Any) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "trace_id": _trace_id(),
        "timestamp": _now().isoformat(),
    }


def error_envelope(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    retryable: bool = False,
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message, "retryable": retryable}
    if details:
        err["details"] = details
    return {
        "success": False,
        "error": err,
        "trace_id": _trace_id(),
        "timestamp": _now().isoformat(),
    }


class APIError(BaseModel):
    """Generic API error used to surface typed failures from routes."""

    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None