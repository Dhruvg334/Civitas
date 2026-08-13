from __future__ import annotations

from typing import Any

import pytest

from civitas_knowledge.backends import HttpKnowledgeBackend
from civitas_knowledge.contracts import PolicyType
from civitas_knowledge.errors import KnowledgeMalformedResponseError


class FakeTransport:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def get_json(
        self, url: str, *, headers: dict[str, str], timeout_seconds: float
    ) -> tuple[int, object]:
        self.calls.append((url, headers, timeout_seconds))
        return self.status, self.payload


def _envelope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "data": {"policies": [row], "count": 1},
        "trace_id": "api-trace",
        "timestamp": "2026-08-13T00:00:00+00:00",
    }


def test_http_adapter_consumes_current_policy_route() -> None:
    transport = FakeTransport(
        _envelope(
            {
                "policy_id": "ply-water-01",
                "code": "PLAY-WATER-01",
                "kind": "playbook",
                "title": "Water playbook",
                "body": "Primary WATER.",
                "categories": ["water_leakage"],
                "departments": ["water"],
                "severity_factors": [],
                "priority_factors": [],
                "required_actions": ["isolate leak"],
                "suggested_resources": ["water crew"],
            }
        )
    )
    backend = HttpKnowledgeBackend(
        base_url="https://civitas.test",
        token="test-token",
        timeout_seconds=7,
        transport=transport,
    )
    records = backend.list_records(policy_type=PolicyType.PLAYBOOK)
    url, headers, timeout = transport.calls[0]
    assert url == "https://civitas.test/api/v1/policies?limit=200&kind=playbook"
    assert headers["Authorization"] == "Bearer test-token"
    assert timeout == 7
    assert records[0].reference_id == "PLAY-WATER-01"
    assert records[0].provenance.source_identifier == "ply-water-01"


def test_http_adapter_rejects_malformed_envelope() -> None:
    backend = HttpKnowledgeBackend(
        base_url="https://civitas.test", transport=FakeTransport({"policies": []})
    )
    with pytest.raises(KnowledgeMalformedResponseError):
        backend.list_records()
