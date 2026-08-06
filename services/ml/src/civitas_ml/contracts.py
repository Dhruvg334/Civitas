from typing import Literal

from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    primary_category: str | None = None
    observable_evidence: list[str] = Field(default_factory=list)
    media_quality: Literal["good", "limited", "unusable"]
    uncertainty: list[str] = Field(default_factory=list)


class DuplicateResult(BaseModel):
    is_duplicate: bool
    matched_incident_id: str | None = None
    score: float = Field(ge=0, le=1)
    feature_contributions: dict[str, float | int | bool | str] = Field(default_factory=dict)
    decision_basis: list[str] = Field(default_factory=list)
