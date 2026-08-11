"""Spatial endpoint tests.

These tests cover the four geospatial routes identified by the integration
plan.  We use an in-memory SQLite stand-in so the routes are exercised
without a live PostGIS instance; the same code path runs against real
PostgreSQL/PostGIS in production (and in integration tests against
`DATABASE_URL=postgresql://...`).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from civitas_api.main import app


def _seed_incidents(client: TestClient, payloads: list[dict], auth_header: dict[str, str]) -> list[str]:
    ids: list[str] = []
    for p in payloads:
        r = client.post("/api/v1/reports", json=p, headers=auth_header)
        assert r.status_code == 201, r.text
        ids.append(r.json()["data"]["report_id"])
    return ids


def test_incidents_nearby_returns_envelope(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/incidents/nearby",
        params={"lat": 20.2961, "lon": 85.8245, "radius_m": 500, "limit": 25},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert body["data"]["mode"] in {"memory", "postgis", "unavailable"}


def test_incidents_nearby_rejects_placeholder(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/incidents/nearby",
        params={"lat": 0.0, "lon": 0.0, "radius_m": 500},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "LOCATION_PLACEHOLDER"


def test_incidents_nearby_validates_lat_range(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/incidents/nearby",
        params={"lat": 999, "lon": 0, "radius_m": 500},
        headers=auth_header,
    )
    assert response.status_code == 422


def test_incident_candidates_404_on_unknown(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get("/api/v1/incidents/inc-doesnotexist/candidates", headers=auth_header)
    assert response.status_code == 404


def test_incident_candidates_returns_envelope_for_known(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    ids = _seed_incidents(client, [
        {"description": "water on road near gate", "location": {"latitude": 20.2961, "longitude": 85.8245}, "citizen_selected_category": "water_leakage"},
        {"description": "more water near same spot", "location": {"latitude": 20.2962, "longitude": 85.8246}, "citizen_selected_category": "water_leakage"},
    ], auth_header)
    response = client.get(
        f"/api/v1/incidents/{ids[0]}/candidates",
        params={"radius_m": 500, "within_hours": 72},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body
    assert body["data"]["mode"] in {"memory", "postgis", "unavailable"}


def test_landmarks_nearby_returns_envelope(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/landmarks/nearby",
        params={"lat": 20.2961, "lon": 85.8245, "radius_m": 50_000, "limit": 5},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "landmarks" in body["data"]
    assert isinstance(body["data"]["landmarks"], list)


def test_landmarks_nearby_kind_filter(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/landmarks/nearby",
        params={"lat": 20.2961, "lon": 85.8245, "radius_m": 50_000, "kind": "school", "limit": 5},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    for lm in body["data"]["landmarks"]:
        assert lm["kind"] == "school"


def test_incidents_nearby_density_returns_envelope(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get(
        "/api/v1/incidents/nearby/density",
        params={"cell_size_m": 200},
        headers=auth_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["mode"] in {"memory", "postgis", "unavailable"}
