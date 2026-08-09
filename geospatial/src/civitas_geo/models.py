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


class OperationalBoundary(BaseModel):
    """The spatial boundary of an operational area (PostGIS Boundary).

    Phase 2 artifact: one shared boundary definition consumed by location
    validation (gate for spatial pipeline) and by every candidate retrieval
    query (envelope pre-filter on the geometry column). Bounding-box for now;
    the model is forward-compatible with polygon boundaries.
    """

    name: str
    bbox: tuple[float, float, float, float] = (
        28.55, 77.15, 28.66, 77.27
    )
    source: str = "config"

    def contains(self, latitude: float, longitude: float) -> bool:
        min_lat, min_lon, max_lat, max_lon = self.bbox
        return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon

    @property
    def description(self) -> str:
        min_lat, min_lon, max_lat, max_lon = self.bbox
        return (
            f"{self.name} boundary [{min_lat:.3f},{min_lon:.3f}]"
            f"..[{max_lat:.3f},{max_lon:.3f}] (source: {self.source})"
        )


class CandidateSearchSpec(BaseModel):
    """Retrieval windows the ML models need (Phase 2): nearby reports within
    X metres and reported within Y hours, plus category/exclusion filters."""

    center: GeoPoint
    radius_m: float = Field(gt=0, le=50_000)
    within_hours: float = Field(default=168.0, gt=0, le=8_760)
    limit: int = Field(default=25, ge=1, le=200)
    exclude_incident_ids: list[str] = Field(default_factory=list)
    category_filter: str | None = None


class CandidateRecord(BaseModel):
    """One enriched candidate fed to the ML duplicate engine.

    Carries every spatial field the models consume: coordinates, distance,
    timestamps, category, repetition count, time-window flag, and the
    landmark/context distances used by duplicate and exposure features.
    """

    incident_id: str
    latitude: float
    longitude: float
    category: str | None = None
    distance_m: float = Field(ge=0)
    reported_at: datetime | None = None
    duplicates_seen: int = Field(default=1, ge=1)
    hours_since_reported: float | None = Field(default=None, ge=0)
    within_time_window: bool = True
    landmark_context: list[LandmarkDistance] = Field(default_factory=list)


class CandidateListResult(BaseModel):
    """Spatial-stage output for the duplicate engine: ordered candidate list."""

    center: GeoPoint
    radius_m: float = Field(gt=0)
    within_hours: float = Field(gt=0)
    candidates: list[CandidateRecord] = Field(default_factory=list)
    total_in_window: int = Field(default=0, ge=0)
    mode: Literal["postgis", "memory", "unavailable"] = "memory"
    boundary: OperationalBoundary | None = None
    basis: list[str] = Field(default_factory=list)


class PipelineGateDecision(BaseModel):
    """Location-validation gate: is a report geographically plausible enough
    to enter the spatial/retrieval pipeline (Phase 2)."""

    can_enter: bool
    reason: Literal[
        "approved",
        "rejected_malformed",
        "rejected_placeholder",
        "rejected_out_of_coverage",
        "rejected_implausible",
    ]
    warnings: list[str] = Field(default_factory=list)
    validation: LocationValidationResult | None = None


class DensityCell(BaseModel):
    """One grid cell with its observed report count (Phase 4).

    The cell key derives from the snapped coordinate pair (ST_SnapToGrid
    alignment in postgis mode; identical floor-anchored math in memory mode)
    so both modes produce the same cell_id for the same physical cell.
    """

    cell_id: str
    anchor_lat: float
    anchor_lon: float
    center_lat: float
    center_lon: float
    cell_span_m: float = Field(gt=0)
    report_count: int = Field(ge=0)
    category_distribution: dict[str, int] = Field(default_factory=dict)


class DensityAggregateResult(BaseModel):
    """Reports-per-cell transactional density aggregate (Phase 4).

    Represents the cell's density window (count of reports landed in that
    cell over the configured recency window and cell size) plus the
    per-category breakdown. Mode labels the geometry provenance exactly like
    the Phase 2 candidate retrieval stages.
    """

    cell_size_m: float = Field(gt=0)
    cells: list[DensityCell] = Field(default_factory=list)
    total_reports: int = Field(default=0, ge=0)
    window_hours: float | None = Field(default=None, ge=0)
    mode: Literal["postgis", "memory", "unavailable"] = "memory"
    basis: list[str] = Field(default_factory=list)

    def top_cells(self, limit: int = 5) -> list[DensityCell]:
        """Cells with the highest report counts, descending."""
        return sorted(self.cells, key=lambda c: c.report_count, reverse=True)[:limit]

    def cell_count(self) -> int:
        return len(self.cells)


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