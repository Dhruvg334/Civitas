from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import pytest
from pydantic import BaseModel, ConfigDict

from civitas_workflow.llm.client import FakeLLMClient, GroqLLMClient
from civitas_workflow.llm.config import LLMSettings
from civitas_workflow.llm.contracts import LLMMessage, LLMUsage, TransportResponse
from civitas_workflow.llm.errors import (
    LLMConfigurationError,
    LLMMalformedJSONError,
    LLMRetriesExhaustedError,
    LLMSchemaValidationError,
    LLMTimeoutError,
)
from civitas_workflow.llm.tracing import InMemoryTraceSink


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: str
    reference_ids: list[str]


class SequenceTransport:
    def __init__(self, responses: Sequence[TransportResponse | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> TransportResponse:
        self.calls.append(
            {"url": url, "headers": headers, "payload": payload, "timeout": timeout_seconds}
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _settings(*, retries: int = 0, api_key: str | None = "secret") -> LLMSettings:
    return LLMSettings(
        api_key=api_key,
        primary_model="configured-primary",
        fast_model="configured-fast",
        timeout_seconds=3.5,
        max_retries=retries,
        temperature=0,
        strict_json_schema=False,
        groq_base_url="https://groq.test/openai/v1",
    )


def _success(
    content: object,
    *,
    model: str = "returned-model",
    usage: dict[str, int] | None = None,
) -> TransportResponse:
    return TransportResponse(
        status_code=200,
        payload={
            "id": "req-123",
            "model": model,
            "choices": [{"message": {"content": content}}],
            "usage": usage or {},
        },
        headers={"x-request-id": "header-request-id"},
    )


MESSAGES = [LLMMessage(role="user", content="Return a structured decision.")]


def test_missing_api_configuration_fails_when_call_attempted() -> None:
    client = GroqLLMClient(_settings(api_key=None), transport=SequenceTransport([]))
    with pytest.raises(LLMConfigurationError, match="GROQ_API_KEY"):
        client.generate_structured(MESSAGES, Decision)


def test_environment_configuration_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "env-secret")
    monkeypatch.setenv("CIVITAS_LLM_PRIMARY_MODEL", "primary-from-env")
    monkeypatch.setenv("CIVITAS_LLM_FAST_MODEL", "fast-from-env")
    monkeypatch.setenv("CIVITAS_LLM_TIMEOUT_SECONDS", "4.5")
    monkeypatch.setenv("CIVITAS_LLM_MAX_RETRIES", "3")
    monkeypatch.setenv("CIVITAS_LLM_TEMPERATURE", "0.2")
    monkeypatch.setenv("CIVITAS_LLM_STRICT_JSON_SCHEMA", "true")
    settings = LLMSettings.from_env()
    assert settings.primary_model == "primary-from-env"
    assert settings.fast_model == "fast-from-env"
    assert settings.timeout_seconds == 4.5
    assert settings.max_retries == 3
    assert settings.temperature == 0.2
    assert settings.strict_json_schema is True


def test_successful_structured_result_uses_injected_transport() -> None:
    transport = SequenceTransport(
        [
            _success(
                json.dumps({"action": "review", "reference_ids": ["POL-GEN-05"]}),
                usage={"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
            )
        ]
    )
    result = GroqLLMClient(_settings(), transport=transport).generate_structured(
        MESSAGES, Decision, trace_id="trc-explicit"
    )
    assert result.output.action == "review"
    assert result.provider == "groq"
    assert result.model == "returned-model"
    assert result.usage == LLMUsage(input_tokens=11, output_tokens=7, total_tokens=18)
    assert result.trace_id == "trc-explicit"
    request = transport.calls[0]
    assert request["payload"]["response_format"]["type"] == "json_schema"
    assert request["payload"]["response_format"]["json_schema"]["strict"] is False
    assert request["headers"]["Authorization"] == "Bearer secret"


def test_malformed_model_json_is_rejected() -> None:
    client = GroqLLMClient(_settings(), transport=SequenceTransport([_success("not-json")]))
    with pytest.raises(LLMMalformedJSONError):
        client.generate_structured(MESSAGES, Decision)


def test_schema_failure_is_rejected() -> None:
    client = GroqLLMClient(
        _settings(),
        transport=SequenceTransport([_success(json.dumps({"action": "review"}))]),
    )
    with pytest.raises(LLMSchemaValidationError) as exc_info:
        client.generate_structured(MESSAGES, Decision)
    assert exc_info.value.details["errors"]


def test_retryable_provider_error_then_success() -> None:
    transport = SequenceTransport(
        [
            TransportResponse(status_code=503, payload={"error": {"message": "busy"}}),
            _success(json.dumps({"action": "review", "reference_ids": []})),
        ]
    )
    result = GroqLLMClient(_settings(retries=2), transport=transport).generate_structured(
        MESSAGES, Decision
    )
    assert result.retry_count == 1
    assert len(transport.calls) == 2


def test_exhausted_retries_has_distinct_error() -> None:
    transport = SequenceTransport(
        [TransportResponse(status_code=503, payload={}) for _ in range(3)]
    )
    client = GroqLLMClient(_settings(retries=2), transport=transport)
    with pytest.raises(LLMRetriesExhaustedError) as exc_info:
        client.generate_structured(MESSAGES, Decision)
    assert exc_info.value.retry_count == 2
    assert exc_info.value.details["last_error_code"] == "llm_provider_failure"


def test_timeout_handling_without_retries() -> None:
    client = GroqLLMClient(
        _settings(retries=0), transport=SequenceTransport([TimeoutError("slow")])
    )
    with pytest.raises(LLMTimeoutError):
        client.generate_structured(MESSAGES, Decision)


def test_metadata_and_trace_capture() -> None:
    sink = InMemoryTraceSink()
    client = GroqLLMClient(
        _settings(),
        transport=SequenceTransport(
            [_success(json.dumps({"action": "review", "reference_ids": []}))]
        ),
        trace_sink=sink,
    )
    result = client.generate_structured(MESSAGES, Decision, trace_id="trc-42")
    assert result.provider_metadata == {"request_id": "header-request-id"}
    event = sink.events[0]
    assert event.trace_id == "trc-42"
    assert event.provider == "groq"
    assert event.status == "succeeded"
    assert event.validation_result == "valid"


def test_failure_trace_does_not_capture_auth_or_content() -> None:
    sink = InMemoryTraceSink()
    client = GroqLLMClient(
        _settings(), transport=SequenceTransport([_success("bad-json")]), trace_sink=sink
    )
    with pytest.raises(LLMMalformedJSONError):
        client.generate_structured(MESSAGES, Decision, trace_id="trc-bad")
    serialized = sink.events[0].model_dump_json()
    assert "secret" not in serialized
    assert "Return a structured decision" not in serialized
    assert sink.events[0].error_code == "llm_malformed_json"


def test_fake_provider_is_deterministic_and_schema_validating() -> None:
    client = FakeLLMClient({"action": "review", "reference_ids": ["POL-1"]})
    first = client.generate_structured(MESSAGES, Decision)
    second = client.generate_structured(MESSAGES, Decision)
    assert first == second
    assert first.trace_id == "trc-fake-deterministic"
    assert first.provider == "fake"
    assert first.provider_metadata["deterministic"] is True


def test_fake_provider_rejects_invalid_output() -> None:
    with pytest.raises(LLMSchemaValidationError):
        FakeLLMClient({"action": "review"}).generate_structured(MESSAGES, Decision)
