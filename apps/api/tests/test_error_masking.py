"""Tests for production error masking and OpenAPI docs hiding."""

import json

import pytest
from starlette.requests import Request

from civitas_api.core import config as cfg
from civitas_api.main import unhandled_exception_handler


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


@pytest.mark.anyio
async def test_production_error_masking_handler(monkeypatch) -> None:
    # Set production environment with valid production settings
    _set_mock_production_env(monkeypatch)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/broken",
        "headers": [],
    }
    request = Request(scope)
    exc = RuntimeError("Sensitive DB connection string: postgresql://admin:secret@10.0.0.1/db")
    response = await unhandled_exception_handler(request, exc)

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["success"] is False
    assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert body["error"]["message"] == "An unexpected server error occurred. Please contact support."
    # Verify sensitive error message is masked and not exposed
    assert "postgresql" not in response.body.decode()
    assert "secret" not in response.body.decode()
    assert "Sensitive" not in response.body.decode()

    cfg.get_settings.cache_clear()


@pytest.mark.anyio
async def test_development_error_handler_shows_detail(monkeypatch) -> None:
    # In development mode, detailed error is returned
    monkeypatch.setenv("CIVITAS_ENV", "development")
    cfg.get_settings.cache_clear()

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/broken",
        "headers": [],
    }
    request = Request(scope)
    exc = RuntimeError("Dev debug error detail")
    response = await unhandled_exception_handler(request, exc)

    assert response.status_code == 500
    body = json.loads(response.body)
    assert body["success"] is False
    assert "Dev debug error detail" in body["error"]["message"]

    cfg.get_settings.cache_clear()

