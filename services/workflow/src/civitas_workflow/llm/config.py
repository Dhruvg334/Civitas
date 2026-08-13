"""Environment-backed Groq LLM configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from civitas_workflow.llm.errors import LLMConfigurationError


@dataclass(frozen=True)
class LLMSettings:
    api_key: str | None = None
    primary_model: str | None = None
    fast_model: str | None = None
    timeout_seconds: float = 20.0
    max_retries: int = 2
    temperature: float = 0.0
    strict_json_schema: bool = False
    groq_base_url: str = "https://api.groq.com/openai/v1"

    @classmethod
    def from_env(cls) -> LLMSettings:
        timeout = _float_env("CIVITAS_LLM_TIMEOUT_SECONDS", 20.0, minimum=0.001)
        retries = _int_env("CIVITAS_LLM_MAX_RETRIES", 2, minimum=0)
        temperature = _float_env("CIVITAS_LLM_TEMPERATURE", 0.0, minimum=0.0)
        if temperature > 2:
            raise LLMConfigurationError("CIVITAS_LLM_TEMPERATURE must be <= 2")
        primary = os.environ.get("CIVITAS_LLM_PRIMARY_MODEL") or None
        return cls(
            api_key=os.environ.get("GROQ_API_KEY") or None,
            primary_model=primary,
            fast_model=os.environ.get("CIVITAS_LLM_FAST_MODEL") or primary,
            timeout_seconds=timeout,
            max_retries=retries,
            temperature=temperature,
            strict_json_schema=_bool_env("CIVITAS_LLM_STRICT_JSON_SCHEMA", False),
            groq_base_url=os.environ.get(
                "CIVITAS_GROQ_BASE_URL", "https://api.groq.com/openai/v1"
            ).rstrip("/"),
        )

    def model_for(self, tier: str) -> str:
        model = (self.fast_model or self.primary_model) if tier == "fast" else self.primary_model
        if not model:
            variable = (
                "CIVITAS_LLM_FAST_MODEL or CIVITAS_LLM_PRIMARY_MODEL"
                if tier == "fast"
                else "CIVITAS_LLM_PRIMARY_MODEL"
            )
            raise LLMConfigurationError(f"{variable} is required for this LLM call")
        return model

    def require_api_key(self) -> str:
        if not self.api_key:
            raise LLMConfigurationError(
                "GROQ_API_KEY is required when a Groq LLM call is attempted"
            )
        return self.api_key


def _float_env(name: str, default: float, *, minimum: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        raise LLMConfigurationError(f"{name} must be a number, got {raw!r}") from None
    if value < minimum:
        raise LLMConfigurationError(f"{name} must be >= {minimum}, got {raw!r}")
    return value


def _int_env(name: str, default: int, *, minimum: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        raise LLMConfigurationError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise LLMConfigurationError(f"{name} must be >= {minimum}, got {raw!r}")
    return value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise LLMConfigurationError(f"{name} must be true or false, got {raw!r}")
