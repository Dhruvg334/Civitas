from __future__ import annotations

from civitas_api.core.config import Settings


def _create_report(client, auth_header, description, lat, lon, category):
    response = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={
            "description": description,
            "location": {"latitude": lat, "longitude": lon},
            "citizen_selected_category": category,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    return payload["data"]["report_id"], payload["data"]["submitted_at"]


def test_internal_nearby_candidates_returns_ml_contract(client, auth_header):
    first, submitted = _create_report(
        client, auth_header, "water leaking near school gate", 28.6000, 77.2000, "water leakage"
    )
    second, _ = _create_report(
        client, auth_header, "road flooding near the same school", 28.6004, 77.2004, "water leakage"
    )
    response = client.post(
        "/api/v1/ml/nearby-candidates",
        json={
            "report_id": first,
            "latitude": 28.6000,
            "longitude": 77.2000,
            "submitted_at": submitted,
            "category": "water_leakage",
            "radius_m": 2000,
            "time_window_h": 72,
            "limit": 25,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["request"]["report_id"] == first
    ids = {c["report_id"] for c in data["candidates"]}
    assert second in ids
    assert first not in ids


def test_internal_landmarks_uses_standard_envelope(client):
    response = client.get("/api/v1/ml/landmarks")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "landmarks" in payload["data"]


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_production_requires_auth_and_internal_secrets():
    try:
        Settings(environment="production", supabase_jwt_secret="", civitas_internal_api_key="")
    except Exception as exc:
        message = str(exc)
        assert "SUPABASE_JWT_SECRET" in message or "CIVITAS_INTERNAL_API_KEY" in message
    else:
        raise AssertionError("production settings accepted missing security secrets")
