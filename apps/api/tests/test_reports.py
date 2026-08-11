from fastapi.testclient import TestClient


def _payload() -> dict:
    return {
        "description": "Water is leaking across the road near the school gate.",
        "location": {"latitude": 20.3534, "longitude": 85.8195},
        "citizen_selected_category": "water_leakage",
    }


def test_create_report_persists_and_envelopes(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.post("/api/v1/reports", json=_payload(), headers=auth_header)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["status"] == "submitted"
    assert data["latitude"] == 20.3534
    assert data["longitude"] == 85.8195
    assert data["category"] == "water_leakage"
    assert data["report_id"].startswith("inc-")


def test_create_report_validates_latitude_range(client: TestClient, auth_header: dict[str, str]) -> None:
    bad = _payload()
    bad["location"]["latitude"] = 1000.0
    response = client.post("/api/v1/reports", json=bad, headers=auth_header)
    assert response.status_code == 422


def test_get_report_round_trip(client: TestClient, auth_header: dict[str, str]) -> None:
    created = client.post("/api/v1/reports", json=_payload(), headers=auth_header).json()
    report_id = created["data"]["report_id"]
    fetched = client.get(f"/api/v1/reports/{report_id}", headers=auth_header)
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["success"] is True
    assert body["data"]["report_id"] == report_id


def test_get_unknown_report_returns_404(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get("/api/v1/reports/inc-doesnotexist", headers=auth_header)
    assert response.status_code == 404
