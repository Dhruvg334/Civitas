"""Tests for media upload route: POST /api/v1/reports/{id}/media.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from civitas_api.main import app


def _create_report(client: TestClient, auth_header: dict[str, str]) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "report",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["report_id"]


def test_upload_image_persists_and_returns_signed_url(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    rid = _create_report(client, auth_header)
    # 1x1 PNG bytes
    png_hex = (
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63f8cfc0500f0000020001f5a356a4000000004945"
        "4e44ae426082"
    )
    png_bytes = bytes.fromhex(png_hex)
    files = {"file": ("dot.png", png_bytes, "image/png")}
    r = client.post(
        f"/api/v1/reports/{rid}/media",
        headers=auth_header,
        files=files,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["kind"] == "image"
    assert data["mime_type"] == "image/png"
    assert data["bytes_size"] == len(png_bytes)
    assert data["media_id"].startswith("med-")
    assert data["signed_url"].startswith("local://") or data["signed_url"].startswith("https://")


def test_upload_rejects_unsupported_mime(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    rid = _create_report(client, auth_header)
    files = {"file": ("evil.exe", b"MZ\x90\x00", "application/x-msdownload")}
    r = client.post(f"/api/v1/reports/{rid}/media", headers=auth_header, files=files)
    assert r.status_code == 415
    body = r.json()
    assert body["detail"]["error"]["code"] == "UNSUPPORTED_MEDIA"


def test_upload_rejects_empty_file(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    rid = _create_report(client, auth_header)
    files = {"file": ("empty.png", b"", "image/png")}
    r = client.post(f"/api/v1/reports/{rid}/media", headers=auth_header, files=files)
    assert r.status_code == 400
    body = r.json()
    assert body["detail"]["error"]["code"] == "EMPTY_FILE"


def test_upload_requires_auth(client: TestClient, storage_root) -> None:
    files = {"file": ("dot.png", b"x", "image/png")}
    r = client.post("/api/v1/reports/inc-anything/media", files=files)
    assert r.status_code == 401


def test_upload_404_on_unknown_report(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    files = {"file": ("dot.png", b"x", "image/png")}
    r = client.post(
        "/api/v1/reports/inc-nope/media",
        headers=auth_header,
        files=files,
    )
    assert r.status_code == 404
