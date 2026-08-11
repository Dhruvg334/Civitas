"""Tests for the work-order lifecycle routes:

    POST   /api/v1/incidents/{incident_id}/work-orders
    GET    /api/v1/work-orders/{work_order_id}
    PUT    /api/v1/work-orders/{work_order_id}
    POST   /api/v1/work-orders/{work_order_id}/approve
    POST   /api/v1/work-orders/{work_order_id}/reject
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from civitas_api.main import app


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
    return r.json()["data"]["report_id"]


def _reviewer_token() -> str:
    import jwt as pyjwt
    return pyjwt.encode(
        {"sub": "reviewer-1", "role": "reviewer"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _reviewer_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {_reviewer_token()}"}


def test_create_work_order_advances_incident(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={
            "summary": "Inspect water leak",
            "required_actions": ["secure area", "isolate leak"],
            "suggested_resources": ["water crew"],
            "safety_notes": ["check slip risk"],
            "primary_department": "water_supply",
            "secondary_departments": ["traffic_coordination"],
            "escalation_required": False,
            "policy_references": ["PLAY-WATER-01"],
            "estimated_window_min_hours": 8,
            "estimated_window_max_hours": 14,
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["work_order_id"].startswith("wo-")
    assert data["incident_id"] == rid
    assert data["status"] == "awaiting_review"
    assert data["primary_department"] == "water_supply"
    assert data["required_actions"] == ["secure area", "isolate leak"]
    assert bool(data["non_binding"]) is True

    # Incident moved to awaiting_review
    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "awaiting_review"
    assert det["assigned_department"] == "water_supply"


def test_create_work_order_404_on_unknown_incident(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    r = client.post(
        "/api/v1/incidents/inc-nope/work-orders",
        json={"summary": "x"},
        headers=auth_header,
    )
    assert r.status_code == 404


def test_create_work_order_validates_summary(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/work-orders", json={}, headers=auth_header
    )
    assert r.status_code == 422
    body = r.json()
    assert body["detail"]["code"] == "VALIDATION_ERROR"


def test_create_work_order_requires_supervisor(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    import jwt as pyjwt
    citizen_tok = pyjwt.encode(
        {"sub": "c-1", "role": "citizen"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )
    r = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x"},
        headers={"Authorization": f"Bearer {citizen_tok}"},
    )
    assert r.status_code == 403


def test_get_work_order_envelope(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "test"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    r = client.get(f"/api/v1/work-orders/{wid}", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["data"]["work_order_id"] == wid


def test_get_work_order_404(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.get("/api/v1/work-orders/wo-nope", headers=auth_header)
    assert r.status_code == 404


def test_update_work_order_patches_fields(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "before"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    r = client.put(
        f"/api/v1/work-orders/{wid}",
        json={"summary": "after", "primary_department": "water_supply"},
        headers=auth_header,
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["summary"] == "after"
    assert data["primary_department"] == "water_supply"


def test_approve_advances_incident_to_assigned(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x", "primary_department": "water_supply"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    r = client.post(
        f"/api/v1/work-orders/{wid}/approve",
        headers=_reviewer_header(),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["status"] == "approved"
    assert data["reviewed_by"] == "reviewer-1"
    assert data["reviewed_at"] is not None

    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "assigned"
    assert det["assigned_work_order_id"] == wid


def test_approve_requires_reviewer(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    # supervisor (auth_header) cannot approve
    r = client.post(
        f"/api/v1/work-orders/{wid}/approve", headers=auth_header
    )
    assert r.status_code == 403


def test_approve_409_after_approval(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    rh = _reviewer_header()
    client.post(f"/api/v1/work-orders/{wid}/approve", headers=rh)
    r = client.post(f"/api/v1/work-orders/{wid}/approve", headers=rh)
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "INVALID_STATE"


def test_reject_moves_incident_to_rejected_wo_stays(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    r = client.post(f"/api/v1/work-orders/{wid}/reject", headers=_reviewer_header())
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    # WO stays in awaiting_review
    assert data["status"] == "awaiting_review"
    assert data["reviewed_by"] == "reviewer-1"

    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "rejected"


def test_reject_409_when_already_approved(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    cr = client.post(
        f"/api/v1/incidents/{rid}/work-orders",
        json={"summary": "x"},
        headers=auth_header,
    )
    wid = cr.json()["data"]["work_order_id"]
    rh = _reviewer_header()
    client.post(f"/api/v1/work-orders/{wid}/approve", headers=rh)
    r = client.post(f"/api/v1/work-orders/{wid}/reject", headers=rh)
    assert r.status_code == 409