"""Backend adapter configuration.

The ML module never hard-codes backend URLs, credentials or endpoint
paths. Mode and connection settings come from the environment:

    CIVITAS_BACKEND_MODE            mock | real        (default: mock)
    CIVITAS_BACKEND_BASE_URL        https://api...     (required for real)
    CIVITAS_BACKEND_API_TOKEN       <token>            (optional bearer auth)
    CIVITAS_INTERNAL_API_KEY         <key>              (server-to-server key)
    CIVITAS_BACKEND_TIMEOUT_SECONDS 10                 (per-request timeout)

The safe default is `mock`: the full pipeline runs locally against
deterministic fixtures with no backend service at all.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from civitas_ml.errors import CODE_CONFIG_ERROR, MLServiceError

if TYPE_CHECKING:
    from civitas_ml.adapters.base import BackendAdapter

MODE_MOCK = "mock"
MODE_REAL = "real"


@dataclass(frozen=True)
class BackendSettings:
    """Resolved backend settings (never read secrets into the ML models)."""

    mode: str = MODE_MOCK
    base_url: str | None = None
    api_token: str | None = None
    timeout_seconds: float = 10.0
    extra_headers: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_env() -> BackendSettings:
        mode = os.environ.get("CIVITAS_BACKEND_MODE", MODE_MOCK).strip().lower()
        if mode not in (MODE_MOCK, MODE_REAL):
            raise MLServiceError(
                f"CIVITAS_BACKEND_MODE must be 'mock' or 'real', got {mode!r}",
                code=CODE_CONFIG_ERROR,
            )
        timeout_raw = os.environ.get("CIVITAS_BACKEND_TIMEOUT_SECONDS", "10")
        try:
            timeout = float(timeout_raw)
        except ValueError:
            raise MLServiceError(
                f"CIVITAS_BACKEND_TIMEOUT_SECONDS must be a number, got {timeout_raw!r}",
                code=CODE_CONFIG_ERROR,
            ) from None
        if timeout <= 0:
            raise MLServiceError(
                f"CIVITAS_BACKEND_TIMEOUT_SECONDS must be > 0, got {timeout_raw!r}",
                code=CODE_CONFIG_ERROR,
            )
        headers: dict[str, str] = {}
        internal_key = os.environ.get("CIVITAS_INTERNAL_API_KEY") or None
        if internal_key:
            headers["X-Civitas-Internal-Key"] = internal_key
        return BackendSettings(
            mode=mode,
            base_url=os.environ.get("CIVITAS_BACKEND_BASE_URL") or None,
            api_token=os.environ.get("CIVITAS_BACKEND_API_TOKEN") or None,
            timeout_seconds=timeout,
            extra_headers=headers,
        )

    def require_base_url(self) -> str:
        if not self.base_url:
            raise MLServiceError(
                "CIVITAS_BACKEND_MODE=real requires CIVITAS_BACKEND_BASE_URL "
                "to be set (the endpoint base of the backend API)",
                code=CODE_CONFIG_ERROR,
            )
        return self.base_url


def get_backend(settings: BackendSettings | None = None) -> BackendAdapter:
    """Build the backend adapter selected by configuration.

    Defaults to the deterministic mock adapter so local execution and the
    test suite never depend on an external service.
    """
    from civitas_ml.adapters.mock import MockBackendAdapter
    from civitas_ml.adapters.real_http import RealBackendAdapter

    cfg = settings or BackendSettings.from_env()
    if cfg.mode == MODE_REAL:
        return RealBackendAdapter(base_url=cfg.require_base_url(), token=cfg.api_token, timeout_seconds=cfg.timeout_seconds, extra_headers=cfg.extra_headers)
    return MockBackendAdapter()


__all__ = [
    "MODE_MOCK",
    "MODE_REAL",
    "BackendSettings",
    "get_backend",
]