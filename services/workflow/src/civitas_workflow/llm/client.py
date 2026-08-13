"""Provider-neutral structured generation plus Groq and deterministic fake clients."""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any, Literal, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ValidationError

from civitas_workflow.llm.config import LLMSettings
from civitas_workflow.llm.contracts import (
    LLMMessage,
    LLMResult,
    LLMTraceRecord,
    LLMUsage,
    ModelTier,
    TransportResponse,
)
from civitas_workflow.llm.errors import (
    LLMError,
    LLMMalformedJSONError,
    LLMProviderError,
    LLMRetriesExhaustedError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from civitas_workflow.llm.tracing import LLMTraceSink, NullTraceSink
from civitas_workflow.llm.transport import LLMTransport, UrllibLLMTransport

OutputT = TypeVar("OutputT", bound=BaseModel)
Clock = Callable[[], float]


class LLMClient(ABC):
    @abstractmethod
    def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        output_type: type[OutputT],
        *,
        model_tier: ModelTier = ModelTier.PRIMARY,
        trace_id: str | None = None,
    ) -> LLMResult[OutputT]: ...


class GroqLLMClient(LLMClient):
    """Groq implementation hidden behind the provider-neutral client contract."""

    provider = "groq"

    def __init__(
        self,
        settings: LLMSettings | None = None,
        *,
        transport: LLMTransport | None = None,
        trace_sink: LLMTraceSink | None = None,
        clock: Clock = time.perf_counter,
    ) -> None:
        self.settings = settings or LLMSettings.from_env()
        self.transport = transport or UrllibLLMTransport()
        self.trace_sink = trace_sink or NullTraceSink()
        self.clock = clock

    def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        output_type: type[OutputT],
        *,
        model_tier: ModelTier = ModelTier.PRIMARY,
        trace_id: str | None = None,
    ) -> LLMResult[OutputT]:
        call_trace_id = trace_id or f"trc-{uuid4().hex}"
        started = self.clock()
        retry_count = 0
        model = "unconfigured"
        try:
            api_key = self.settings.require_api_key()
            model = self.settings.model_for(model_tier.value)
            while True:
                try:
                    response = self.transport.post_json(
                        f"{self.settings.groq_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                        },
                        payload=_request_payload(
                            messages,
                            output_type,
                            model,
                            self.settings.temperature,
                            self.settings.strict_json_schema,
                        ),
                        timeout_seconds=self.settings.timeout_seconds,
                    )
                    result = self._parse_response(
                        response,
                        output_type,
                        model=model,
                        trace_id=call_trace_id,
                        retry_count=retry_count,
                        started=started,
                    )
                    self._record_success(result)
                    return result
                except TimeoutError as exc:
                    error: LLMError = LLMTimeoutError(
                        "Groq request timed out", trace_id=call_trace_id
                    )
                    error.__cause__ = exc
                except ConnectionError as exc:
                    error = LLMProviderError(
                        "Groq provider is unreachable",
                        trace_id=call_trace_id,
                        retryable=True,
                    )
                    error.__cause__ = exc
                except LLMProviderError as exc:
                    error = exc

                if not error.retryable:
                    raise error
                if retry_count >= self.settings.max_retries:
                    if retry_count == 0:
                        raise error
                    raise LLMRetriesExhaustedError(
                        "Groq call exhausted configured retries",
                        last_error=error,
                        retry_count=retry_count,
                    )
                retry_count += 1
        except LLMError as exc:
            self._record_failure(exc, model, call_trace_id, retry_count, started)
            raise

    def _parse_response(
        self,
        response: TransportResponse,
        output_type: type[OutputT],
        *,
        model: str,
        trace_id: str,
        retry_count: int,
        started: float,
    ) -> LLMResult[OutputT]:
        if response.status_code >= 400:
            retryable = response.status_code == 429 or response.status_code >= 500
            raise LLMProviderError(
                f"Groq returned HTTP {response.status_code}",
                trace_id=trace_id,
                retryable=retryable,
                details={"status_code": response.status_code},
            )
        if response.payload is None:
            raise LLMMalformedJSONError("Groq returned a non-JSON response", trace_id=trace_id)
        try:
            choice = response.payload["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Groq response is missing choices[0].message.content",
                trace_id=trace_id,
            ) from exc
        try:
            raw_output = json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError as exc:
            raise LLMMalformedJSONError(
                "Groq model output is not valid JSON", trace_id=trace_id
            ) from exc
        try:
            output = output_type.model_validate(raw_output)
        except ValidationError as exc:
            raise LLMSchemaValidationError(
                "Groq model output failed schema validation",
                trace_id=trace_id,
                details={"errors": exc.errors(include_url=False)},
            ) from exc

        actual_model = str(response.payload.get("model") or model)
        usage = _usage(response.payload.get("usage"))
        metadata: dict[str, str | int | float | bool | None] = {}
        request_id = response.headers.get("x-request-id") or response.payload.get("id")
        if request_id is not None:
            metadata["request_id"] = str(request_id)
        fingerprint = response.payload.get("system_fingerprint")
        if fingerprint is not None:
            metadata["system_fingerprint"] = str(fingerprint)
        return LLMResult[OutputT](
            output=output,
            provider=self.provider,
            model=actual_model,
            latency_ms=_elapsed_ms(self.clock, started),
            usage=usage,
            trace_id=trace_id,
            retry_count=retry_count,
            provider_metadata=metadata,
        )

    def _record_success(self, result: LLMResult[Any]) -> None:
        self.trace_sink.record(
            LLMTraceRecord(
                trace_id=result.trace_id,
                provider=result.provider,
                model=result.model,
                latency_ms=result.latency_ms,
                status="succeeded",
                retry_count=result.retry_count,
                usage=result.usage,
                validation_result="valid",
                provider_metadata=result.provider_metadata,
            )
        )

    def _record_failure(
        self,
        error: LLMError,
        model: str,
        trace_id: str,
        retry_count: int,
        started: float,
    ) -> None:
        validation: Literal["valid", "invalid", "not_attempted"] = (
            "invalid"
            if isinstance(error, (LLMMalformedJSONError, LLMSchemaValidationError))
            else "not_attempted"
        )
        self.trace_sink.record(
            LLMTraceRecord(
                trace_id=trace_id,
                provider=self.provider,
                model=model,
                latency_ms=_elapsed_ms(self.clock, started),
                status="failed",
                retry_count=retry_count,
                validation_result=validation,
                error_code=error.code,
            )
        )


class FakeLLMClient(LLMClient):
    """Deterministic offline provider that still enforces output schemas."""

    provider = "fake"

    def __init__(
        self,
        output: BaseModel | dict[str, Any] | str,
        *,
        model: str = "fake-structured-v1",
        usage: LLMUsage | None = None,
        latency_ms: int = 0,
    ) -> None:
        self._output = output
        self.model = model
        self.usage = usage
        self.latency_ms = latency_ms

    def generate_structured(
        self,
        messages: Sequence[LLMMessage],
        output_type: type[OutputT],
        *,
        model_tier: ModelTier = ModelTier.PRIMARY,
        trace_id: str | None = None,
    ) -> LLMResult[OutputT]:
        del messages, model_tier
        call_trace_id = trace_id or "trc-fake-deterministic"
        raw = (
            self._output.model_dump(mode="json")
            if isinstance(self._output, BaseModel)
            else self._output
        )
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise LLMMalformedJSONError(
                    "Fake LLM output is not valid JSON", trace_id=call_trace_id
                ) from exc
        try:
            output = output_type.model_validate(raw)
        except ValidationError as exc:
            raise LLMSchemaValidationError(
                "Fake LLM output failed schema validation",
                trace_id=call_trace_id,
                details={"errors": exc.errors(include_url=False)},
            ) from exc
        return LLMResult[OutputT](
            output=output,
            provider=self.provider,
            model=self.model,
            latency_ms=self.latency_ms,
            usage=self.usage,
            trace_id=call_trace_id,
            retry_count=0,
            provider_metadata={"deterministic": True},
        )


def _request_payload(
    messages: Sequence[LLMMessage],
    output_type: type[BaseModel],
    model: str,
    temperature: float,
    strict_json_schema: bool,
) -> dict[str, object]:
    return {
        "model": model,
        "messages": [message.model_dump(mode="json") for message in messages],
        "temperature": temperature,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": output_type.__name__,
                "strict": strict_json_schema,
                "schema": output_type.model_json_schema(),
            },
        },
    }


def _usage(raw: object) -> LLMUsage | None:
    if not isinstance(raw, dict):
        return None
    return LLMUsage(
        input_tokens=_optional_int(raw.get("prompt_tokens")),
        output_tokens=_optional_int(raw.get("completion_tokens")),
        total_tokens=_optional_int(raw.get("total_tokens")),
    )


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _elapsed_ms(clock: Clock, started: float) -> int:
    return max(0, round((clock() - started) * 1000))


__all__ = ["FakeLLMClient", "GroqLLMClient", "LLMClient"]
