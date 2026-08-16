from __future__ import annotations

from fastapi.testclient import TestClient

from civitas_api.core.config import Settings


def test_analyze_report_internal_route(client: TestClient, auth_header: dict[str, str]) -> None:
    created = client.post(
        "/api/v1/reports",
        json={
            "description": "water leaking beside a school",
            "location": {"latitude": 20.2, "longitude": 85.8},
        },
        headers=auth_header,
    )
    report_id = created.json()["data"]["report_id"]
    result = client.post(
        "/api/v1/ml/analyze", json={"report_id": report_id, "trace_id": "trace-ml"}
    )
    assert result.status_code == 200
    data = result.json()["data"]
    assert data["report_id"] == report_id
    assert data["trace_id"] == "trace-ml"
    assert {"vision", "duplicate", "cluster", "severity", "priority", "models"} <= data.keys()


def test_analyze_unknown_report_is_404(client: TestClient) -> None:
    assert client.post("/api/v1/ml/analyze", json={"report_id": "missing"}).status_code == 404


def _create_report(client, auth_header, description, lat, lon, category):
    response = client.post(
        "/api/v1/reports",
        headers=auth_header,
        json={
            "description": description,
            "location": {"latitude": lat, "longitude": lon},
            "citizen_selected_category": category,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    return payload["data"]["report_id"], payload["data"]["submitted_at"]


def test_internal_nearby_candidates_returns_ml_contract(client, auth_header):
    first, submitted = _create_report(
        client, auth_header, "water leaking near school gate", 28.6000, 77.2000, "water leakage"
    )
    second, _ = _create_report(
        client, auth_header, "road flooding near the same school", 28.6004, 77.2004, "water leakage"
    )
    response = client.post(
        "/api/v1/ml/nearby-candidates",
        json={
            "report_id": first,
            "latitude": 28.6000,
            "longitude": 77.2000,
            "submitted_at": submitted,
            "category": "water_leakage",
            "radius_m": 2000,
            "time_window_h": 72,
            "limit": 25,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["request"]["report_id"] == first
    ids = {c["report_id"] for c in data["candidates"]}
    assert second in ids
    assert first not in ids


def test_internal_landmarks_uses_standard_envelope(client):
    response = client.get("/api/v1/ml/landmarks")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "landmarks" in payload["data"]


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_production_requires_complete_runtime_security_configuration():
    import pytest

    with pytest.raises(Exception) as exc_info:
        Settings(
            environment="production",
            database_url="",
            civitas_postgis_dsn="",
            supabase_url="",
            supabase_service_role_key="",
            civitas_internal_api_key="",
            workflow_checkpoint_database_url="",
            groq_api_key="",
        )

    message = str(exc_info.value)
    for required in (
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "CIVITAS_POSTGIS_DSN",
        "CIVITAS_INTERNAL_API_KEY",
        "CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL",
        "GROQ_API_KEY",
    ):
        assert required in message


def test_production_rejects_wildcard_cors():
    import pytest

    with pytest.raises(Exception, match="CORS_ORIGINS"):
        Settings(
            environment="production",
            cors_origins="*",
            database_url="postgresql://db/civitas",
            civitas_postgis_dsn="postgresql://db/civitas",
            supabase_url="https://project.supabase.co",
            supabase_service_role_key="server-only",
            civitas_internal_api_key="internal",
            workflow_checkpoint_database_url="postgresql://db/checkpoints",
            groq_api_key="groq-key",
        )


def test_uploaded_image_is_consumed_by_internal_ml_pipeline(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    from io import BytesIO

    from PIL import Image

    report_id, _ = _create_report(
        client,
        auth_header,
        "water pooled beside a school entrance",
        20.2961,
        85.8245,
        "water_leakage",
    )
    buffer = BytesIO()
    Image.new("RGB", (128, 128), color=(90, 120, 135)).save(buffer, format="PNG")
    upload = client.post(
        f"/api/v1/reports/{report_id}/media",
        headers=auth_header,
        files={"file": ("scene.png", buffer.getvalue(), "image/png")},
    )
    assert upload.status_code == 201, upload.text

    result = client.post("/api/v1/ml/analyze", json={"report_id": report_id})
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["vision"]["media_kind"] == "image"
