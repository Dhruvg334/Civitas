"""Shared typed contracts for Civitas geospatial intelligence.

These models keep observable geography (points, landmarks, distances),
retrieved spatial context and inference (exposure, validation warnings)
distinct so downstream consumers can attribute each signal.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

GeoRichType = Literal[
    "school", "hospital", "junction", "market", "park", "waterbody", "metro_station", "pathway"
]
LandmarkKind = GeoRichType

Plausibility = Literal["plausible", "implausible", "uncertain"]


class GeoPoint(BaseModel):
    """A validated geographic coordinate."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)


class Landmark(BaseModel):
    """A named point of interest used for grounding and exposure."""

    model_config = ConfigDict(frozen=True)

    landmark_id: str
    name: str
    kind: LandmarkKind
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=100.0, ge=0)


class LandmarkDistance(BaseModel):
    """Distance from a point to its nearest landmark of a kind."""

    landmark: Landmark
    distance_m: float = Field(ge=0)


class LocationValidationResult(BaseModel):
    """Output of location validation. Warnings are heuristics, never asserted facts."""

    point: GeoPoint
    is_valid: bool
    plausibility: Plausibility
    warnings: list[str] = Field(default_factory=list)
    suggested_snap: GeoPoint | None = None
    basis: list[str] = Field(default_factory=list)


class NearbyIncident(BaseModel):
    """A retrieved incident record returned by the spatial layer."""

    incident_id: str
    latitude: float
    longitude: float
    category: str | None = None
    distance_m: float = Field(ge=0)
    reported_at: datetime | None = None
    duplicates_seen: int = Field(default=1, ge=1)


class NearbyIncidentsResult(BaseModel):
    """Spatial retrieval response, indexed for map display and clustering."""

    center: GeoPoint
    radius_m: float = Field(gt=0)
    incidents: list[NearbyIncident] = Field(default_factory=list)
    total_in_radius: int = Field(default=0, ge=0)
    mode: Literal["postgis", "memory", "unavailable"] = "memory"
    basis: list[str] = Field(default_factory=list)


class ExposureContext(BaseModel):
    """Map-based reasoning output used by severity/priority feature engineering."""

    nearest_school_m: float | None = None
    nearest_hospital_m: float | None = None
    junction_density_1km: float = Field(default=0.0, ge=0)
    nearest_waterbody_m: float | None = None
    pathway_proximity: bool = False
    traffic_exposure: Literal["low", "moderate", "high"] = "moderate"
    sources: list[str] = Field(default_factory=list)
    inference: list[str] = Field(default_factory=list)


class SpatialSearchSpec(BaseModel):
    """Input contract for PostGIS-backed spatial queries."""

    center: GeoPoint
    radius_m: float = Field(gt=0, le=50_000)
    limit: int = Field(default=25, ge=1, le=200)
    exclude_incident_ids: list[str] = Field(default_factory=list)
    category_filter: str | None = None
    since: datetime | None = None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def geo_kwargs(**kwargs: Any) -> dict[str, Any]:
    """Helper for tests and builders; kept trivial on purpose."""
    return kwargs