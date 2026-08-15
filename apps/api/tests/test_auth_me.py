"""Tests for GET /api/v1/me."""

def test_get_me_unauthorized(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 401


def test_get_me_authenticated(client, auth_header):
    r = client.get("/api/v1/me", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["user_id"] == "test-user"
    assert data["data"]["role"] == "supervisor"
