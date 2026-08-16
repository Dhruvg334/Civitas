"""Tests for the resolutions module."""

from __future__ import annotations

import jwt as pyjwt
from fastapi.testclient import TestClient


def _supervisor_token() -> str:
    return pyjwt.encode(
        {"sub": "sup-1", "role": "supervisor"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _triage_token() -> str:
    return pyjwt.encode(
        {"sub": "tri-1", "role": "triage"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _reviewer_token() -> str:
    return pyjwt.encode(
        {"sub": "rev-1", "role": "reviewer"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _hdr(tok: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {tok}"}


def _drive_to_in_progress(client: TestClient, rid: str, auth: dict[str, str]) -> str:
    """Walk an incident through: submitted -> awaiting_review -> assigned -> in_progress.
    Returns the work_order_id."""
    wo = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "fix it", "primary_department": "water_supply"},
        headers=auth,
    ).json()["data"]
    wid = wo["work_order_id"]
    # Approve as reviewer -> assigned
    client.post(f"/api/v1/work-orders/{wid}/approve", headers=_hdr(_reviewer_token()))
    # The WO then auto-progresses; to reach in_progress we'd need a 'start work'
    # route which isn't in scope. For tests, jump straight: approve_work_order
    # already moved it to assigned. We'll add an internal helper that drives
    # assigned -> in_progress via direct DB update.
    from civitas_api.core.database import get_connection
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE incidents SET status='in_progress', status_updated_at=datetime('now') WHERE incident_id=%(i)s",
            {"i": rid},
        )
        conn.commit()
    return wid


def test_submit_resolution_validates_classification(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "water on road",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    _drive_to_in_progress(client, rid, sup)

    r = client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={"classification": "bogus"},
        headers=_hdr(_triage_token()),
    )
    assert r.status_code == 422


def test_submit_resolution_persists_and_advances(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "water on road",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    _drive_to_in_progress(client, rid, sup)

    r = client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={
            "classification": "partially_resolved",
            "resolved_evidence": ["active flow no longer visible"],
            "remaining_evidence": ["standing water remains near footpath"],
            "uncertainties": ["drainage condition outside frame"],
            "model_version": "resolution-verify-v1",
        },
        headers=_hdr(_triage_token()),
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["classification"] == "partially_resolved"
    assert data["resolution_id"].startswith("rsl-")
    assert data["resolved_evidence"] == ["active flow no longer visible"]

    det = client.get(f"/api/v1/incidents/{rid}", headers=sup).json()["data"]
    assert det["status"] == "verification_pending"
    assert det["resolution_class"] == "partially_resolved"


def test_submit_resolution_409_if_not_in_progress(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "fresh report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "pothole",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    # Don't drive to in_progress
    r = client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={"classification": "resolved"},
        headers=_hdr(_triage_token()),
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "INVALID_STATE"


def test_reviewer_resolve_moves_to_resolved(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "fresh report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "pothole",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    # Drive to verification_pending first
    _drive_to_in_progress(client, rid, sup)
    client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={"classification": "resolved"},
        headers=_hdr(_triage_token()),
    )
    # Now reviewer closes
    r = client.post(
        f"/api/v1/incidents/{rid}/resolve",
        json={"action": "resolved"},
        headers=_hdr(_reviewer_token()),
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["status"] == "resolved"


def test_reviewer_resolve_partially_resolved_and_reopened(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "fresh report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "pothole",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    _drive_to_in_progress(client, rid, sup)
    client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={"classification": "partially_resolved"},
        headers=_hdr(_triage_token()),
    )
    r = client.post(
        f"/api/v1/incidents/{rid}/resolve",
        json={"action": "partially_resolved"},
        headers=_hdr(_reviewer_token()),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "partially_resolved"

    # Now reopen -> under_analysis
    r = client.post(
        f"/api/v1/incidents/{rid}/resolve",
        json={"action": "reopened"},
        headers=_hdr(_reviewer_token()),
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "reopened"


def test_list_resolution_submissions(
    client: TestClient,
) -> None:
    sup = _hdr(_supervisor_token())
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "fresh report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "pothole",
        },
        headers=sup,
    )
    rid = r.json()["data"]["report_id"]
    _drive_to_in_progress(client, rid, sup)
    client.post(
        f"/api/v1/incidents/{rid}/resolution-submissions",
        json={"classification": "resolved"},
        headers=_hdr(_triage_token()),
    )
    r = client.get(f"/api/v1/incidents/{rid}/resolution-submissions", headers=sup)
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 1