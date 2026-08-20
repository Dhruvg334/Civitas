"""Security tests for media upload: magic bytes verification, spoofed MIME rejection, path traversal."""

from fastapi.testclient import TestClient


def _create_report(client: TestClient, auth_header: dict[str, str]) -> str:
    r = client.post(
        "/api/v1/reports",
        json={
            "description": "Security test report for media",
            "location": {"latitude": 20.2961, "longitude": 85.8245},
            "citizen_selected_category": "water_leakage",
        },
        headers=auth_header,
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["report_id"]


def test_upload_rejects_spoofed_mime_type(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    rid = _create_report(client, auth_header)

    # Spoofed PNG: Content-Type is image/png but payload is malicious HTML/script
    spoofed_bytes = b"<script>alert('XSS')</script>"
    files = {"file": ("malicious.png", spoofed_bytes, "image/png")}

    r = client.post(f"/api/v1/reports/{rid}/media", headers=auth_header, files=files)
    assert r.status_code == 415
    body = r.json()
    assert body["detail"]["error"]["code"] == "INVALID_FILE_SIGNATURE"


def test_upload_accepts_valid_magic_bytes_jpeg(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    rid = _create_report(client, auth_header)

    # Valid JPEG magic bytes (\xFF\xD8\xFF)
    jpeg_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb"
    files = {"file": ("photo.jpg", jpeg_bytes, "image/jpeg")}

    r = client.post(f"/api/v1/reports/{rid}/media", headers=auth_header, files=files)
    assert r.status_code == 201
    body = r.json()
    assert body["success"] is True
    assert body["data"]["mime_type"] == "image/jpeg"


def test_upload_rejects_path_traversal_report_id(
    client: TestClient, auth_header: dict[str, str], storage_root
) -> None:
    # Attempt path traversal via report_id
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63f8cfc0500f0000020001f5a356a4000000004945"
        "4e44ae426082"
    )
    files = {"file": ("dot.png", png_bytes, "image/png")}

    r = client.post("/api/v1/reports/..%2F..%2Fetc/media", headers=auth_header, files=files)
    assert r.status_code in {400, 404}
