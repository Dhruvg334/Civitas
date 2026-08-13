from __future__ import annotations

import json

import pytest

from civitas_workflow.http_adapters import (
    HTTPAdapterSettings,
    HttpReportContextTool,
    HttpTraceTool,
    WorkflowHTTPError,
)
from civitas_workflow.workflow_contracts import WorkflowTraceEvent


class FakeTransport:
    def __init__(self, responses: dict[str, tuple[int, object]]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, str, dict[str, str]]] = []

    def request(
        self, method: str, url: str, *, headers: dict[str, str], body: bytes | None, timeout: float
    ) -> tuple[int, bytes]:
        del body, timeout
        self.requests.append((method, url, headers))
        status, response = self.responses[f"{method} {url}"]
        return status, json.dumps(response).encode()


def _settings() -> HTTPAdapterSettings:
    return HTTPAdapterSettings("http://api", "http://ml", internal_api_key="not-a-secret")


def test_report_context_adapter_validates_existing_envelopes() -> None:
    transport = FakeTransport(
        {
            "GET http://api/api/v1/reports/r1": (
                200,
                {
                    "success": True,
                    "data": {
                        "report_id": "r1",
                        "description": "water leak",
                        "latitude": 20.2,
                        "longitude": 85.8,
                        "category": "water_leak",
                    },
                },
            ),
            "GET http://api/api/v1/reports/r1/media": (
                200,
                {"success": True, "data": {"media": []}},
            ),
            "GET http://api/api/v1/reports/r1/clarifications": (
                200,
                {
                    "success": True,
                    "data": {
                        "clarifications": [
                            {
                                "question_id": "q1",
                                "answered_at": "now",
                                "answer_text": "near school",
                            }
                        ]
                    },
                },
            ),
        }
    )
    context = HttpReportContextTool(_settings(), transport).load("r1")
    assert context.incident_id == "r1"
    assert context.clarification_answers == {"q1": "near school"}


def test_adapter_raises_typed_error_for_runtime_failure() -> None:
    transport = FakeTransport(
        {"GET http://api/api/v1/reports/missing": (404, {"detail": "not found"})}
    )
    with pytest.raises(WorkflowHTTPError) as exc:
        HttpReportContextTool(_settings(), transport).load("missing")
    assert exc.value.code == "HTTP_ERROR"


def test_trace_adapter_propagates_trace_id_without_secret() -> None:
    transport = FakeTransport(
        {"POST http://api/api/v1/incidents/i1/trace": (200, {"success": True, "data": {}})}
    )
    HttpTraceTool(_settings(), transport).record(
        "i1", "trace-1", WorkflowTraceEvent(node="node", status="succeeded", latency_ms=1)
    )
    assert transport.requests[0][2]["X-Civitas-Trace-Id"] == "trace-1"
    assert "not-a-secret" not in str(WorkflowTraceEvent(node="node", status="succeeded", latency_ms=1))
