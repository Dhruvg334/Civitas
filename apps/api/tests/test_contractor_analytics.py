"""Unit and integration tests for municipal contractor scorecard and SLA analytics."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_evaluation.contractor_analytics import compute_contractor_scorecard

client = TestClient(app)


def test_compute_contractor_scorecard_perfect():
    records = [
        {"status": "resolved", "duration_hours": 8.0, "sla_target_hours": 24.0, "is_disputed": False},
        {"status": "resolved", "duration_hours": 12.0, "sla_target_hours": 24.0, "is_disputed": False},
    ]
    sc = compute_contractor_scorecard("CONT-01", "water_supply", records)
    assert sc.completed_jobs == 2
    assert sc.sla_compliance_rate_pct == 100.0
    assert sc.dispute_count == 0
    assert sc.composite_performance_score >= 85.0
    assert sc.performance_tier == "TIER_1_EXCELLENT"


def test_compute_contractor_scorecard_underperforming():
    records = [
        {"status": "resolved", "duration_hours": 36.0, "sla_target_hours": 24.0, "is_disputed": True},
        {"status": "reopened_disputed", "duration_hours": 48.0, "sla_target_hours": 24.0, "is_disputed": True},
    ]
    sc = compute_contractor_scorecard("CONT-02", "road_maintenance", records)
    assert sc.sla_compliance_rate_pct == 0.0
    assert sc.dispute_count == 2
    assert sc.composite_performance_score < 70.0
    assert sc.performance_tier == "TIER_3_UNDERPERFORMING"


def test_contractor_analytics_endpoint():
    resp = client.get("/analytics/contractors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "scorecards" in data["data"]
    assert isinstance(data["data"]["scorecards"], list)
    if data["data"]["scorecards"]:
        first = data["data"]["scorecards"][0]
        assert "composite_performance_score" in first
        assert "sla_compliance_rate_pct" in first
