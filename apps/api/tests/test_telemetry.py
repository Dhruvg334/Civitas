"""Integration tests for SCADA and IoT municipal telemetry router."""

from fastapi.testclient import TestClient
from civitas_api.main import app

client = TestClient(app)


def test_ingest_scada_telemetry_anomaly():
    payload = {
        "sensor_id": "SCADA-WAT-099",
        "sensor_type": "water_pressure",
        "reading_value": 15.2,  # Major drop below 45 psi normal
        "threshold_value": 45.0,
        "unit": "psi",
        "latitude": 20.29614,
        "longitude": 85.82451,
    }
    resp = client.post("/telemetry/scada", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["sensor_id"] == "SCADA-WAT-099"
    assert data["data"]["is_anomaly"] is True
    assert data["data"]["status"] == "ANOMALY_CORRELATED"
    assert "hex_cell_id" in data["data"]


def test_list_municipal_sensors():
    resp = client.get("/telemetry/sensors")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    sensors = data["data"]
    assert len(sensors) >= 3


def test_get_hex_density_endpoint():
    resp = client.get("/telemetry/hex-density", params={"latitude": 20.29614, "longitude": 85.82451, "resolution": 8})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "cell_id" in data["data"]
    assert "is_chronic_failure_zone" in data["data"]
