"""Unit and integration tests for Bill of Quantities (BOQ) cost estimation."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_ml.boq_costing import generate_boq_estimate

client = TestClient(app)


def test_generate_boq_pothole():
    boq = generate_boq_estimate(
        category="pothole_road_damage",
        area_cm2=2500.0,
        depth_mm=75.0,
        is_emergency=False,
    )
    assert boq.defect_area_m2 == 0.25
    assert len(boq.line_items) >= 4
    assert boq.subtotal_inr > 0.0
    assert boq.total_estimated_cost_inr > boq.subtotal_inr  # Includes contingency
    assert boq.total_estimated_cost_usd > 0.0
    assert boq.estimated_repair_duration_hours >= 2.0


def test_generate_boq_water_leak():
    boq = generate_boq_estimate(
        category="water_leakage",
        area_cm2=5000.0,
        depth_mm=100.0,
        is_emergency=True,
    )
    assert boq.contingency_inr == round(boq.subtotal_inr * 0.15, 2)
    assert any("Ductile Iron" in item.description or "Sleeve" in item.description for item in boq.line_items)


def test_boq_estimate_endpoint():
    payload = {
        "category": "broken_streetlight",
        "defect_area_cm2": 500.0,
        "defect_depth_mm": 10.0,
        "is_emergency": False,
    }
    resp = client.post("/work-orders/boq-estimate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "line_items" in data["data"]
    assert len(data["data"]["line_items"]) >= 3
    assert data["data"]["total_estimated_cost_inr"] > 0.0


def test_generate_boq_zero_dimensions_and_unknown_category():
    boq = generate_boq_estimate(
        category="unknown_exotic_hazard",
        area_cm2=0.0,
        depth_mm=0.0,
        is_emergency=False,
    )
    assert boq.defect_area_m2 >= 0.1
    assert boq.total_estimated_cost_inr > 0.0
    assert len(boq.line_items) >= 2
