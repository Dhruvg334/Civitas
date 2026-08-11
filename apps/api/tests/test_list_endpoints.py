"""Tests for the list endpoints:

    GET /api/v1/incidents
    GET /api/v1/reports/{id}/media
"""

from __future__ import annotations

import base64

import jwt as pyjwt
from fastapi.testclient import TestClient

from civitas_api.main import app


def _sup_token() -> str:
    return pyjwt.encode(
        {"sub": "sup-1", "role": "supervisor"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _triage_token() -> str:
    return pyjwt.encode(
        {"sub": "tri-1", "role": "triage"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )


def _sup_hdr() -> dict[str, str]:
    return {"Authorization": f"Bearer {_sup_token()}"}


def _triage_hdr() -> dict[str, str]:
    return {"Authorization": f"Bearer {_triage_token()}"}


def _create_report(client: TestClient, hdr: dict[str, str], desc: str) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": desc,
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["report_id"]


def test_list_incidents_empty(client: TestClient) -> None:
    r = client.get("/api/v1/incidents", headers=_triage_hdr())
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 0


def test_list_incidents_returns_reports(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    _create_report(client, auth_header, "first report")
    _create_report(client, auth_header, "second report")
    r = client.get("/api/v1/incidents", headers=_triage_hdr())
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] == 2


def test_list_incidents_filter_by_status(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    rid = _create_report(client, auth_header, "to be merged")
    _create_report(client, auth_header, "untouched")
    # Merge one to move it to 'clustered'
    client.post(
        f"/api/v1/incidents/{rid}/merge",
        json={"report_id": rid, "confidence": 0.5},
        headers=auth_header,
    )
    # Itself goes to clustered; the second one stays at submitted
    r = client.get(
        "/api/v1/incidents", params={"status": "submitted"}, headers=_triage_hdr()
    )
    assert r.status_code == 200
    data = r.json()["data"]
    # The 'report_id' == 'incident_id' merge creates a self-loop; the incident
    # is still in 'submitted' (after merge 0 rows changed because of the
    # ON CONFLICT).  So both should be submitted.
    for inc in data["incidents"]:
        assert inc["status"] == "submitted"


def test_list_media_empty(client: TestClient, auth_header: dict[str, str]) -> None:
    rid = _create_report(client, auth_header, "no media")
    r = client.get(f"/api/v1/reports/{rid}/media", headers=auth_header)
    assert r.status_code == 200
    assert r.json()["data"]["count"] == 0


def test_list_media_returns_uploaded(
    client: TestClient,
    auth_header: dict[str, str],
    storage_root,
) -> None:
    rid = _create_report(client, auth_header, "with media")
    # 1x1 PNG
    png_hex = (
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63f8cfc0500f0000020001f5a356a4000000004945"
        "4e44ae426082"
    )
    files = {"file": ("dot.png", bytes.fromhex(png_hex), "image/png")}
    r = client.post(
        f"/api/v1/reports/{rid}/media", headers=auth_header, files=files
    )
    assert r.status_code == 201, r.text

    r = client.get(f"/api/v1/reports/{rid}/media", headers=auth_header)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] == 1
    assert data["media"][0]["mime_type"] == "image/png"
    assert "signed_url" in data["media"][0]


def test_list_media_404(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.get("/api/v1/reports/inc-nope/media", headers=auth_header)
    assert r.status_code == 404