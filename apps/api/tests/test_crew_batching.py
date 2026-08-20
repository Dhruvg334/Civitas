"""Unit and integration tests for spatial work order batching and crew dispatch."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_api.operations.crew_batching import batch_work_orders_by_crew_and_spatial_hex

client = TestClient(app)


def test_batch_work_orders_by_crew_and_spatial_hex():
    sample_work_orders = [
        {
            "work_order_id": "wo-001",
            "assigned_department": "road_maintenance",
            "category": "pothole_road_damage",
            "latitude": 20.29614,
            "longitude": 85.82451,
        },
        {
            "work_order_id": "wo-002",
            "assigned_department": "road_maintenance",
            "category": "pothole_road_damage",
            "latitude": 20.29620,
            "longitude": 85.82455,  # Same hex cell
        },
        {
            "work_order_id": "wo-003",
            "assigned_department": "water_supply",
            "category": "water_leakage",
            "latitude": 20.29614,
            "longitude": 85.82451,  # Different crew type
        },
    ]

    bundles = batch_work_orders_by_crew_and_spatial_hex(sample_work_orders)
    assert len(bundles) == 2  # 1 for road crew, 1 for water crew

    road_bundle = next(b for b in bundles if "Road" in b.crew_type or "Asphalt" in b.crew_type)
    assert len(road_bundle.work_order_ids) == 2
    assert "wo-001" in road_bundle.work_order_ids
    assert "wo-002" in road_bundle.work_order_ids
    assert road_bundle.total_estimated_cost_inr > 0.0


def test_get_work_order_batches_endpoint():
    resp = client.get("/work-orders/batches")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "bundles" in data["data"]
    assert isinstance(data["data"]["bundles"], list)
