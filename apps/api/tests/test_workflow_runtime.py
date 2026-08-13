from __future__ import annotations

import jwt
from fastapi.testclient import TestClient


def test_workflow_routes_need_a_configured_runtime(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    result = client.post("/api/v1/reports/missing/workflow", headers=auth_header)
    assert result.status_code in {404, 503}


def test_unknown_workflow_returns_not_found(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    result = client.get("/api/v1/workflows/wf-missing", headers=auth_header)
    assert result.status_code in {404, 503}


def test_review_payload_rejects_arbitrary_state(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    reviewer = {"Authorization": f"Bearer {jwt.encode({'sub': 'reviewer', 'role': 'reviewer'}, 'test', algorithm='HS256')}"}
    result = client.post(
        "/api/v1/workflows/wf-missing/review",
        json={"action": "edit", "operational_plan": {"summary": "x", "graph_state": "inject"}},
        headers=reviewer,
    )
    assert result.status_code == 422
