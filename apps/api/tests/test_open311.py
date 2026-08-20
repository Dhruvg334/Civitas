"""Integration tests for Open311 GeoReport v2 API adapter."""

from fastapi.testclient import TestClient
from civitas_api.main import app

client = TestClient(app)


def test_open311_services_list():
    resp = client.get("/open311/v2/services.json")
    assert resp.status_code == 200
    services = resp.json()
    assert isinstance(services, list)
    assert len(services) >= 5
    codes = [s["service_code"] for s in services]
    assert "001" in codes  # Pothole
    assert "002" in codes  # Water leak


def test_open311_request_submission_and_retrieval():
    form_data = {
        "service_code": "002",
        "lat": "20.29614",
        "long": "85.82451",
        "address_string": "14m from DAV Public School Gate",
        "description": "Severe water burst flooding sidewalk",
        "first_name": "Citizen",
        "phone": "555-0199",
    }
    resp = client.post("/open311/v2/requests.json", data=form_data)
    assert resp.status_code == 200
    res_list = resp.json()
    assert isinstance(res_list, list)
    assert len(res_list) == 1
    req = res_list[0]
    assert "service_request_id" in req
    assert req["status"] == "open"
    assert req["service_code"] == "002"

    # Retrieve request
    get_resp = client.get(f"/open311/v2/requests/{req['service_request_id']}.json")
    assert get_resp.status_code == 200
    get_list = get_resp.json()
    assert len(get_list) == 1
    assert get_list[0]["service_request_id"] == req["service_request_id"]
