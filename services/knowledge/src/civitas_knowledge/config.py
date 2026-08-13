"""Configuration for the real knowledge backend adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass

from civitas_knowledge.backends import HttpKnowledgeBackend, KnowledgeBackend
from civitas_knowledge.errors import KnowledgeConfigurationError


@dataclass(frozen=True)
class KnowledgeBackendSettings:
    base_url: str | None = None
    token: str | None = None
    timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> KnowledgeBackendSettings:
        raw_timeout = os.environ.get("CIVITAS_BACKEND_TIMEOUT_SECONDS", "10")
        try:
            timeout = float(raw_timeout)
        except ValueError:
            raise KnowledgeConfigurationError(
                f"CIVITAS_BACKEND_TIMEOUT_SECONDS must be a number, got {raw_timeout!r}"
            ) from None
        if timeout <= 0:
            raise KnowledgeConfigurationError("CIVITAS_BACKEND_TIMEOUT_SECONDS must be > 0")
        return cls(
            base_url=os.environ.get("CIVITAS_BACKEND_BASE_URL") or None,
            token=os.environ.get("CIVITAS_BACKEND_API_TOKEN") or None,
            timeout_seconds=timeout,
        )

    def build(self) -> KnowledgeBackend:
        if not self.base_url:
            raise KnowledgeConfigurationError(
                "CIVITAS_BACKEND_BASE_URL is required for the HTTP knowledge backend"
            )
        return HttpKnowledgeBackend(
            base_url=self.base_url,
            token=self.token,
            timeout_seconds=self.timeout_seconds,
        )
