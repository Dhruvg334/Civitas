"""Structured errors for the ML service (Phase 10).

Every hard failure surfaces as an `MLServiceError` carrying a stable
`code`, a human `message`, optional `details` and a `trace_id` — the same
shape as `schemas/json/common-error.schema.json`. Soft degradations
(missing GPS, missing text, no candidates) are NOT errors: they return
uncertainty inside the sections with the reason in `basis`.
"""

from __future__ import annotations

from civitas_ml.contracts import ErrorPayload

# Stable machine-readable codes (documented in services/ml/README.md).
CODE_MEDIA_NOT_FOUND = "media_not_found"
CODE_MEDIA_UNREADABLE = "media_unreadable"
CODE_MEDIA_UNSUPPORTED = "media_unsupported"
CODE_MEDIA_INVALID_KIND = "media_invalid_kind"
CODE_DEPENDENCY_MISSING = "dependency_missing"
CODE_BACKEND_UNREACHABLE = "backend_unreachable"
CODE_MALFORMED_RESPONSE = "malformed_response"
CODE_CONFIG_ERROR = "config_error"
CODE_INTERNAL = "internal_error"


class MLServiceError(Exception):
    """Base structured error; carries a payload matching the shared schema."""

    code = CODE_INTERNAL

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, str | int | float | bool | list[str]] | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.code
        self.details = details or {}
        self.trace_id = trace_id

    def payload(self) -> ErrorPayload:
        return ErrorPayload(
            code=self.code,
            message=self.message,
            details=self.details,
            trace_id=self.trace_id,
        )


class BackendAdapterError(MLServiceError):
    """The backend returned unavailable/malformed/invalid data."""

    code = CODE_BACKEND_UNREACHABLE


class MalformedResponseError(BackendAdapterError):
    """The backend returned data that does not validate against the contract."""

    code = CODE_MALFORMED_RESPONSE