"""Tests for the Tier-1 incident lifecycle routes:

GET  /api/v1/incidents/{id}
POST /api/v1/incidents/{id}/merge
POST /api/v1/incidents/{id}/assess
GET  /api/v1/incidents/{id}/trace
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_report(client: TestClient, auth_header: dict[str, str]) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "water on road near school gate",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    if body.get("success") is not True:
        import pytest

        pytest.fail(f"create_report envelope: {body}")
    return body["data"]["report_id"]


def test_get_incident_detail_envelope(client: TestClient, auth_header: dict[str, str]) -> None:
    rid = _create_report(client, auth_header)
    r = client.get(f"/api/v1/incidents/{rid}", headers=auth_header)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["incident_id"] == rid
    assert data["status"] == "submitted"
    assert data["media_count"] == 0
    assert data["linked_reports_count"] == 0
    assert data["latest_assessment"] is None
    assert data["assessment_count"] == 0


def test_get_incident_404_on_unknown(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.get("/api/v1/incidents/inc-nope", headers=auth_header)
    assert r.status_code == 404


def test_get_incident_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/incidents/inc-nope")
    assert r.status_code == 401


def test_merge_links_two_incidents(client: TestClient, auth_header: dict[str, str]) -> None:
    target = _create_report(client, auth_header)
    report = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{target}/merge",
        json={"report_id": report, "confidence": 0.91, "basis": {"reason": "near_duplicate"}},
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["success"] is True, body
    data = body["data"]
    assert data["incident_id"] == target
    assert data["report_id"] == report
    assert data["confidence"] == 0.91
    assert data["link_id"].startswith("lnk-")
    assert data["trace_id"].startswith("trc-")

    # Detail should now show linked+1, and the report's status should be 'clustered'.
    det = client.get(f"/api/v1/incidents/{target}", headers=auth_header).json()["data"]
    assert det["linked_reports_count"] == 1
    assert det["duplicates_seen"] >= 2
    rep = client.get(f"/api/v1/incidents/{report}", headers=auth_header).json()["data"]
    assert rep["status"] == "clustered"


def test_merge_is_idempotent(client: TestClient, auth_header: dict[str, str]) -> None:
    target = _create_report(client, auth_header)
    report = _create_report(client, auth_header)
    payload = {"report_id": report, "confidence": 0.5}
    r1 = client.post(f"/api/v1/incidents/{target}/merge", json=payload, headers=auth_header)
    r2 = client.post(f"/api/v1/incidents/{target}/merge", json=payload, headers=auth_header)
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["data"]["link_id"] == r2.json()["data"]["link_id"]


def test_merge_validates_payload(client: TestClient, auth_header: dict[str, str]) -> None:
    target = _create_report(client, auth_header)
    r = client.post(f"/api/v1/incidents/{target}/merge", json={}, headers=auth_header)
    assert r.status_code == 422
    body = r.json()
    assert body["detail"]["error"]["code"] == "VALIDATION_ERROR"


def test_merge_404_on_unknown_target(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.post(
        "/api/v1/incidents/inc-nope/merge",
        json={"report_id": "inc-also-nope"},
        headers=auth_header,
    )
    assert r.status_code == 404


def test_assess_persists_and_updates_state(client: TestClient, auth_header: dict[str, str]) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/assess",
        json={
            "severity": {
                "score": 78,
                "level": "high",
                "factors": [{"name": "slip_hazard", "contribution": 24}],
            },
            "priority": {
                "score": 91,
                "level": "critical",
                "factors": [{"name": "school_proximity", "contribution": 18}],
            },
            "review_required": True,
            "model_version": "risk-v1",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["severity"]["score"] == 78
    assert data["priority"]["level"] == "critical"
    assert data["model_version"] == "risk-v1"

    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "awaiting_review"
    assert det["last_assessment_model"] == "risk-v1"
    assert det["assessment_count"] == 1
    assert det["latest_assessment"]["severity_score"] == 78


def test_assess_404_on_unknown(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.post(
        "/api/v1/incidents/inc-nope/assess",
        json={
            "severity": {"score": 50, "level": "medium"},
            "priority": {"score": 50, "level": "medium"},
        },
        headers=auth_header,
    )
    assert r.status_code == 404


def test_trace_endpoint_orders_events(client: TestClient, auth_header: dict[str, str]) -> None:
    target = _create_report(client, auth_header)
    report = _create_report(client, auth_header)
    client.post(
        f"/api/v1/incidents/{target}/merge", json={"report_id": report}, headers=auth_header
    )
    client.post(
        f"/api/v1/incidents/{target}/assess",
        json={
            "severity": {"score": 60, "level": "medium"},
            "priority": {"score": 70, "level": "high"},
            "model_version": "risk-v1",
        },
        headers=auth_header,
    )
    r = client.get(f"/api/v1/incidents/{target}/trace", headers=auth_header)
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    events = body["data"]["events"]
    nodes = [e["node"] for e in events]
    assert "merge" in nodes
    assert "assess" in nodes
    # Trace is ordered by created_at ASC.
    assert [e["created_at"] for e in events] == sorted([e["created_at"] for e in events])


def test_trace_filter_by_node(client: TestClient, auth_header: dict[str, str]) -> None:
    rid = _create_report(client, auth_header)
    client.post(
        f"/api/v1/incidents/{rid}/assess",
        json={
            "severity": {"score": 60, "level": "medium"},
            "priority": {"score": 70, "level": "high"},
        },
        headers=auth_header,
    )
    r = client.get(f"/api/v1/incidents/{rid}/trace", params={"node": "assess"}, headers=auth_header)
    assert r.status_code == 200
    events = r.json()["data"]["events"]
    assert len(events) == 1
    assert events[0]["node"] == "assess"


def test_workflow_trace_write_persists_safe_node_event(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/trace",
        headers=auth_header,
        json={
            "workflow_trace_id": "wf-123",
            "node": "knowledge_grounding",
            "status": "succeeded",
            "latency_ms": 12,
            "tool_or_model": "KnowledgeTool",
            "validation_outcome": "valid",
            "knowledge_reference_ids": ["PLAY-WATER-01"],
            "warnings": [],
        },
    )
    assert r.status_code == 201, r.text
    events = client.get(f"/api/v1/incidents/{rid}/trace", headers=auth_header).json()["data"][
        "events"
    ]
    event = events[-1]
    assert event["node"] == "knowledge_grounding"
    assert event["latency_ms"] == 12
    assert event["input"] == '{"workflow_trace_id": "wf-123"}'
