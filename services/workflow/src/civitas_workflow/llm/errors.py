"""Stable, typed LLM failures; invalid output is never returned as success."""

from __future__ import annotations

from typing import Any


class LLMError(Exception):
    code = "llm_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id
        self.details = details or {}


class LLMConfigurationError(LLMError):
    code = "llm_configuration_error"


class LLMTimeoutError(LLMError):
    code = "llm_timeout"
    retryable = True


class LLMProviderError(LLMError):
    code = "llm_provider_failure"

    def __init__(self, *args: Any, retryable: bool = False, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.retryable = retryable


class LLMMalformedJSONError(LLMError):
    code = "llm_malformed_json"


class LLMSchemaValidationError(LLMError):
    code = "llm_schema_validation_failure"


class LLMRetriesExhaustedError(LLMError):
    code = "llm_retries_exhausted"

    def __init__(self, message: str, *, last_error: LLMError, retry_count: int) -> None:
        super().__init__(
            message,
            trace_id=last_error.trace_id,
            details={"last_error_code": last_error.code, "retry_count": retry_count},
        )
        self.last_error = last_error
        self.retry_count = retry_count
