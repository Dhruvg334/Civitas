"""Typed contracts shared by every Civitas LLM provider."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelTier(StrEnum):
    PRIMARY = "primary"
    FAST = "fast"


class LLMMessage(StrictModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class LLMUsage(StrictModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class LLMCallMetadata(StrictModel):
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    trace_id: str
    retry_count: int = Field(ge=0)
    status: Literal["succeeded", "failed"]
    validation_result: Literal["valid", "invalid", "not_attempted"]
    usage: LLMUsage | None = None
    warnings: list[str] = Field(default_factory=list)
    provider_metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class LLMResult[OutputT: BaseModel](StrictModel):
    output: OutputT
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    usage: LLMUsage | None = None
    trace_id: str
    retry_count: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
    provider_metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class LLMTraceRecord(StrictModel):
    """Safe trace event compatible with the existing agent trace fields."""

    trace_id: str
    provider: str
    model: str
    latency_ms: int = Field(ge=0)
    status: Literal["succeeded", "failed"]
    retry_count: int = Field(ge=0)
    usage: LLMUsage | None = None
    validation_result: Literal["valid", "invalid", "not_attempted"]
    error_code: str | None = None
    provider_metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class TransportResponse(StrictModel):
    status_code: int
    payload: dict[str, Any] | None = None
    raw_body: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
