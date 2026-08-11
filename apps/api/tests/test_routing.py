"""Tests for the routing module."""

from __future__ import annotations

from fastapi.testclient import TestClient

from civitas_api.main import app


def _create_report(client: TestClient, auth_header: dict[str, str]) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "routing test report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["report_id"]


def test_route_requires_primary_department(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/route",
        json={},
        headers=auth_header,
    )
    assert r.status_code == 422


def test_route_with_review_advances_to_awaiting_review(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/route",
        json={
            "primary_department": "water_supply",
            "secondary_departments": ["traffic_coordination"],
            "policy_references": ["PLAY-WATER-01"],
            "decision_basis": ["active water flow on public road"],
            "review_required": True,
            "workflow_version": "routing-v1",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    assert data["primary_department"] == "water_supply"
    assert data["routing_id"].startswith("rte-")
    assert bool(data["review_required"]) is True

    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "awaiting_review"
    assert det["assigned_department"] == "water_supply"


def test_route_without_review_advances_to_approved(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    r = client.post(
        f"/api/v1/incidents/{rid}/route",
        json={
            "primary_department": "waste",
            "review_required": False,
            "workflow_version": "routing-v1",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    det = client.get(f"/api/v1/incidents/{rid}", headers=auth_header).json()["data"]
    assert det["status"] == "approved"


def test_route_404_on_unknown(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    r = client.post(
        "/api/v1/incidents/inc-nope/route",
        json={"primary_department": "water_supply"},
        headers=auth_header,
    )
    assert r.status_code == 404


def test_list_routings(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header)
    client.post(
        f"/api/v1/incidents/{rid}/route",
        json={"primary_department": "water_supply", "review_required": True},
        headers=auth_header,
    )
    client.post(
        f"/api/v1/incidents/{rid}/route",
        json={"primary_department": "water_supply", "review_required": False},
        headers=auth_header,
    )
    r = client.get(f"/api/v1/incidents/{rid}/route", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 2