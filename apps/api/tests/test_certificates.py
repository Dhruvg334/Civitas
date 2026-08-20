"""Unit and integration tests for cryptographic municipal audit certificates."""

from fastapi.testclient import TestClient
from civitas_api.main import app
from civitas_api.operations.audit_certificate import generate_municipal_audit_certificate

client = TestClient(app)


def test_generate_municipal_audit_certificate():
    # 1. Create an incident
    create_resp = client.post(
        "/open311/v2/requests.json",
        data={"service_code": "002", "description": "Burst municipal pipe on Park Avenue"},
    )
    inc_id = create_resp.json()[0]["service_request_id"]

    cert = generate_municipal_audit_certificate(inc_id)
    assert cert.incident_id == inc_id
    assert isinstance(cert.sha256_cryptographic_digest, str)
    assert len(cert.sha256_cryptographic_digest) == 64
    assert cert.certificate_id.startswith("CERT-CIVITAS-")
    assert "h3_spatial_cell_res8" in cert.lifecycle_payload


def test_certificate_endpoint():
    create_resp = client.post(
        "/open311/v2/requests.json",
        data={"service_code": "001", "description": "Pothole on 4th crossroad"},
    )
    inc_id = create_resp.json()[0]["service_request_id"]

    resp = client.get(f"/resolutions/{inc_id}/certificate")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "sha256_cryptographic_digest" in data["data"]
    assert "certificate_id" in data["data"]
    assert len(data["data"]["sha256_cryptographic_digest"]) == 64
