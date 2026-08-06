from fastapi.testclient import TestClient

from civitas_api.main import app


def test_create_report_skeleton() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/reports",
        json={
            "description": "Water is leaking across the road near the school gate.",
            "location": {"latitude": 20.3534, "longitude": 85.8195},
            "citizen_selected_category": "water_leakage",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "submitted"
    assert body["location"]["latitude"] == 20.3534
