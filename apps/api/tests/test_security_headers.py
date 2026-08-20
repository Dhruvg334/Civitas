"""Tests for defensive HTTP security headers."""

from fastapi.testclient import TestClient


def test_security_headers_present_on_all_responses(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    headers = response.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "max-age=31536000" in (headers.get("Strict-Transport-Security") or "")
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in (headers.get("Permissions-Policy") or "")
    assert "frame-ancestors 'none'" in (headers.get("Content-Security-Policy") or "")
