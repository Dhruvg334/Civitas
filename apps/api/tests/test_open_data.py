"""Unit and integration tests for public GeoJSON and CSV open data endpoints."""

from fastapi.testclient import TestClient
from civitas_api.main import app

client = TestClient(app)


def test_public_geojson_endpoint():
    # Create an incident
    client.post(
        "/open311/v2/requests.json",
        data={"service_code": "001", "description": "Pothole near park call 9876543210"},
    )

    resp = client.get("/public/incidents.geojson")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert len(data["features"]) >= 1

    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert len(feature["geometry"]["coordinates"]) == 2
    assert "9876543210" not in feature["properties"]["description_sanitized"]
    assert feature["properties"]["privacy_preserved"] is True


def test_public_csv_endpoint():
    resp = client.get("/public/incidents.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    content = resp.text
    assert "incident_id,category,status,reported_at" in content
    assert "latitude_jittered,longitude_jittered" in content
