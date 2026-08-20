"""Unit and integration tests for dynamic exposure and priority acceleration."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_ml.priority_acceleration import evaluate_dynamic_priority

client = TestClient(app)


def test_evaluate_dynamic_priority_school_and_hospital():
    res = evaluate_dynamic_priority(
        latitude=20.29614,
        longitude=85.82451,
        base_severity=50,
        base_sla_hours=24,
        school_distance_m=45.0,  # <= 100m -> +25 pts, 0.5x
        hospital_distance_m=120.0,  # <= 250m -> +30 pts, 0.4x
    )
    assert res.dynamic_priority_score >= 80
    assert res.priority_band == "P1_CRITICAL"
    assert res.accelerated_sla_hours <= 5  # 24 * 0.5 * 0.4 = 4.8 -> 5h
    assert len(res.acceleration_factors) == 2


def test_evaluate_dynamic_priority_baseline():
    res = evaluate_dynamic_priority(
        latitude=20.29614,
        longitude=85.82451,
        base_severity=30,
        base_sla_hours=48,
        school_distance_m=1500.0,  # Far away
        hospital_distance_m=3000.0,
    )
    assert res.dynamic_priority_score == 30
    assert res.priority_band == "P4_LOW"
    assert res.accelerated_sla_hours == 48
    assert len(res.acceleration_factors) == 0


def test_priority_accelerate_endpoint():
    payload = {
        "latitude": 20.29614,
        "longitude": 85.82451,
        "base_severity": 55,
        "base_sla_hours": 24,
        "school_distance_m": 80.0,
        "is_arterial_road": True,
    }
    resp = client.post("/work-orders/priority-accelerate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["dynamic_priority_score"] >= 70
    assert data["data"]["accelerated_sla_hours"] < 24
    assert len(data["data"]["acceleration_factors"]) == 2
