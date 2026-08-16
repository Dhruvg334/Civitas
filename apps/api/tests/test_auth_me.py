"""Tests for GET /api/v1/me and Civitas authentication/authorization enforcement."""

import time
from unittest.mock import MagicMock, patch

import jwt as pyjwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from civitas_api.core import config as cfg
from civitas_api.core.auth import _decode_jwt


def _set_mock_production_env(monkeypatch, **overrides) -> None:
    defaults = {
        "CIVITAS_ENV": "production",
        "DATABASE_URL": "postgresql://postgres:pass@db.internal:5432/postgres",
        "CIVITAS_POSTGIS_DSN": "postgresql://postgres:pass@db.internal:5432/postgres",
        "CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL": "postgresql://postgres:pass@db.internal:5432/postgres",
        "SUPABASE_URL": "https://mock-supabase.civitas.internal",
        "SUPABASE_SERVICE_ROLE_KEY": "mock-service-role-key-12345",
        "CIVITAS_INTERNAL_API_KEY": "mock-internal-api-key-12345",
        "GROQ_API_KEY": "mock-groq-api-key-12345",
        "CORS_ORIGINS": "https://civitas-web.vercel.app",
        "SUPABASE_JWT_SECRET": "",
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)
    cfg.get_settings.cache_clear()


def test_get_me_unauthorized(client: TestClient) -> None:
    r = client.get("/api/v1/me")
    assert r.status_code == 401
    assert "detail" in r.json() or "code" in r.json()


def test_get_me_authenticated(client: TestClient, auth_header: dict[str, str]) -> None:
    r = client.get("/api/v1/me", headers=auth_header)
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["user_id"] == "test-user"
    assert data["data"]["role"] == "supervisor"


def test_hs256_verification_valid_and_invalid_signatures(monkeypatch) -> None:
    secret = "production-supabase-jwt-secret-32-bytes!!"
    _set_mock_production_env(monkeypatch, SUPABASE_JWT_SECRET=secret)

    now = int(time.time())
    valid_token = pyjwt.encode(
        {"sub": "user-hs-123", "role": "citizen", "aud": "authenticated", "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    payload = _decode_jwt(valid_token)
    assert payload["sub"] == "user-hs-123"

    wrong_secret_token = pyjwt.encode(
        {"sub": "user-hs-123", "role": "citizen", "aud": "authenticated", "exp": now + 3600},
        "wrong-secret-signature-mismatch!!",
        algorithm="HS256",
    )
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        _decode_jwt(wrong_secret_token)
    assert exc.value.status_code == 401


def test_token_expiration_and_missing_subject(monkeypatch) -> None:
    secret = "production-supabase-jwt-secret-32-bytes!!"
    _set_mock_production_env(monkeypatch, SUPABASE_JWT_SECRET=secret)

    import pytest
    from fastapi import HTTPException

    # Expired token
    past = int(time.time()) - 3600
    expired_token = pyjwt.encode(
        {"sub": "user-expired", "aud": "authenticated", "exp": past},
        secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(expired_token)
    assert exc.value.status_code == 401

    # Missing sub (subject)
    now = int(time.time())
    no_sub_token = pyjwt.encode(
        {"aud": "authenticated", "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(no_sub_token)
    assert exc.value.status_code == 401

    # Wrong audience
    wrong_aud_token = pyjwt.encode(
        {"sub": "user-aud", "aud": "wrong-audience", "exp": now + 3600},
        secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(wrong_aud_token)
    assert exc.value.status_code == 401


def test_asymmetric_rs256_jwks_verification(monkeypatch) -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    supabase_url = "https://mock-supabase.civitas.internal"
    _set_mock_production_env(monkeypatch, SUPABASE_URL=supabase_url, SUPABASE_JWT_SECRET="")

    now = int(time.time())
    token = pyjwt.encode(
        {
            "sub": "user-rs256",
            "role": "reviewer",
            "aud": "authenticated",
            "iss": f"{supabase_url}/auth/v1",
            "exp": now + 3600,
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "mock-key-id", "alg": "RS256"},
    )

    mock_signing_key = MagicMock()
    mock_signing_key.key = public_pem

    with patch("jwt.PyJWKClient.get_signing_key_from_jwt", return_value=mock_signing_key):
        payload = _decode_jwt(token)
        assert payload["sub"] == "user-rs256"
        assert payload["role"] == "reviewer"


def test_production_rejects_unsigned_tokens(monkeypatch) -> None:
    _set_mock_production_env(monkeypatch)

    import pytest
    from fastapi import HTTPException

    unsigned_token = pyjwt.encode(
        {"sub": "attacker", "role": "admin"},
        "fake-secret",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as exc:
        _decode_jwt(unsigned_token)
    assert exc.value.status_code == 401
