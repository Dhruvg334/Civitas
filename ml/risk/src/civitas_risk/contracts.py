"""Typed contracts for severity and priority assessment.

Severity (how dangerous) and priority (how urgent the response must be) are
deliberately separate decisions, each with its own score, contributing
factors and decision basis.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from civitas_geo.models import ExposureContext

SeverityLevel = Literal["low", "medium", "high", "critical"]
PriorityTier = Literal["P4", "P3", "P2", "P1"]

CATEGORIES = ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")


class RiskContext(BaseModel):
    """All observable context used for severity/priority feature engineering."""

    report_id: str
    category: str
    description: str = ""
    exposure: ExposureContext | None = None
    repeated_reports: int = Field(default=1, ge=1)
    open_hours: float = Field(default=0.0, ge=0)
    rain_intensity_mm_h: float | None = Field(default=None, ge=0)
    electrical_risk_text: bool = False
    accessibility_blocked: bool = False


class SeverityResult(BaseModel):
    """How dangerous/harmful the incident is, with contributing factors."""

    report_id: str
    score: float = Field(ge=0, le=1)
    level: SeverityLevel
    contributing_factors: dict[str, float] = Field(default_factory=dict)
    decision_basis: list[str] = Field(default_factory=list)
    model_version: str = "severity-rule-v1"
    ml_blend_weight: float = Field(ge=0, le=1, default=0.0)


class PriorityResult(BaseModel):
    """How urgently the responsible authority should respond."""

    report_id: str
    score: float = Field(ge=0, le=1)
    tier: PriorityTier
    urgency_contributions: dict[str, float] = Field(default_factory=dict)
    decision_basis: list[str] = Field(default_factory=list)
    model_version: str = "priority-rule-v1"
    ml_blend_weight: float = Field(ge=0, le=1, default=0.0)