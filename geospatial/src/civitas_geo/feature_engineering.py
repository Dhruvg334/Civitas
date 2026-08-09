"""Civitas geospatial feature engineering.

The municipality-analog of the GeoGPT terrain feature pipeline: raw spatial
information (coordinates, timestamps, nearby reports, landmarks, context) is
turned into a clean, measurable, normalized feature vector -- the evidence
layer for the severity, priority and duplicate models.

This module NEVER decides a municipal action. It produces:

  - ``features``   : model-facing normalized values in [0, 1] (or 0/1 flags)
  - ``raw``        : the source measurements (metres, counts, hours)
  - ``provenance`` : a per-feature, human-readable source chain
  - ``warnings``   : labelled validity issues, never assertions
  - ``basis``      : trace summary

GeoGPT analog table (engineered terrain -> municipal incident feature):

    elevation           -> location validity / city coverage
    slope               -> traffic exposure (road class, junction density)
    flow accumulation   -> nearby report count + incident density
    wetness             -> waterbody proximity + rain context
    distances           -> school / hospital / landmark proximity
    neighbourhood stats -> repeated reports, time since first report,
                           distance between reports, population proxy
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from civitas_geo import reasoning
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import (
    GeoPoint,
    NearbyIncident,
    NearbyIncidentsResult,
    SpatialSearchSpec,
)
from civitas_geo.retrieval import NearbyRetriever
from civitas_geo.validation import LocationValidator

SCHEMA_VERSION = "civitas-geo-features-v1"

# Canonical categories mirrored from ml/risk for self-contained feature export.
CANONICAL_CATEGORIES = ("pothole", "water_leak", "garbage", "streetlight", "fallen_tree")
CATEGORY_ALIASES: dict[str, str] = {
    "potholes": "pothole",
    "road damage": "pothole",
    "water leak": "water_leak",
    "water leakage": "water_leak",
    "waterlogging": "water_leak",
    "flooding": "water_leak",
    "garbage overflow": "garbage",
    "waste": "garbage",
    "street light": "streetlight",
    "streetlights": "streetlight",
    "fallen tree": "fallen_tree",
    "tree": "fallen_tree",
    "blocked pathway": "fallen_tree",
}

POPULATION_PROXY_KINDS = ("market", "metro_station", "junction")
NEARBY_RADIUS_M = 800.0
VALIDITY_MAP = {"plausible": 1.0, "uncertain": 0.5, "implausible": 0.0}


class CivicIncidentContext(BaseModel):
    """Everything the feature module needs about one candidate incident.

    nearby_reports: spatial retrieval output (NearbyIncident records) within
    the retrieval radius around this point.
    """

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    submitted_at: datetime
    category: str | None = None
    nearby_reports: list[NearbyIncident] = Field(default_factory=list)


class GeospatialFeatureVector(BaseModel):
    """Clean, measurable evidence vector for downstream models."""

    schema_version: str = SCHEMA_VERSION
    features: dict[str, float] = Field(default_factory=dict)
    raw: dict[str, float | int | str] = Field(default_factory=dict)
    provenance: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    basis: list[str] = Field(default_factory=list)

    def feature_names(self) -> list[str]:
        return sorted(self.features)


def _rbf(distance_m: float, sigma_m: float) -> float:
    return math.exp(-((distance_m / sigma_m) ** 2))


def _cap1(v: float) -> float:
    return max(0.0, min(1.0, v))


def normalize_category(category: str | None) -> str | None:
    """Canonical category form (mirrors ml/risk.features.normalize_category)."""
    if not category:
        return None
    key = category.strip().lower()
    if key in CANONICAL_CATEGORIES:
        return key
    return CATEGORY_ALIASES.get(key)


class GeospatialFeatureEngine:
    """Turn raw civic spatial context into an explainable feature vector."""

    def __init__(
        self,
        landmarks: LandmarkIndex | None = None,
        validator: LocationValidator | None = None,
        nearby_radius_m: float = NEARBY_RADIUS_M,
    ) -> None:
        self.landmarks = landmarks or LandmarkIndex()
        self.validator = validator or LocationValidator(landmarks=self.landmarks)
        self.nearby_radius_m = nearby_radius_m

    # -- public API ---------------------------------------------------------

    def compute(self, ctx: CivicIncidentContext) -> GeospatialFeatureVector:
        point = GeoPoint(latitude=ctx.latitude, longitude=ctx.longitude)
        features: dict[str, float] = {}
        raw: dict[str, float | int | str] = {}
        provenance: dict[str, str] = {}
        warnings: list[str] = []
        basis: list[str] = []

        # 1. Location validity -------------------------------------------------
        validity_result = self.validator.validate(point)
        if not validity_result.is_valid:
            warnings.extend(validity_result.warnings)
        features["location_validity"] = VALIDITY_MAP[validity_result.plausibility]
        raw["is_valid_location"] = int(validity_result.is_valid)
        provenance["location_validity"] = "; ".join(validity_result.warnings) or (
            f"plausibility {validity_result.plausibility}"
        )

        # 2. Landmark proximity (GeoGPT "distances") ---------------------------
        school = self.landmarks.nearest_by_kind(point, "school")
        hospital = self.landmarks.nearest_by_kind(point, "hospital")
        any_lm = self.landmarks.nearest(point, max_distance_m=5_000.0)
        water = self.landmarks.nearest_by_kind(point, "waterbody")
        pathway = self.landmarks.nearest_by_kind(point, "pathway")

        school_d = school.distance_m if school else 5_000.0
        hospital_d = hospital.distance_m if hospital else 5_000.0
        landmark_d = any_lm.distance_m if any_lm else 5_000.0
        water_d = water.distance_m if water else 5_000.0
        pathway_prox = 1.0 if pathway and pathway.distance_m <= pathway.landmark.radius_m * 2 else 0.0

        features["school_proximity"] = round(_rbf(school_d, 300.0), 4)
        features["hospital_proximity"] = round(_rbf(hospital_d, 500.0), 4)
        features["landmark_proximity"] = round(_rbf(landmark_d, 200.0), 4)
        features["waterbody_proximity"] = round(_rbf(water_d, 400.0), 4)
        features["pathway_proximity"] = pathway_prox
        raw["school_distance_m"] = round(school_d, 1)
        raw["hospital_distance_m"] = round(hospital_d, 1)
        raw["landmark_distance_m"] = round(landmark_d, 1)
        raw["waterbody_distance_m"] = round(water_d, 1)
        provenance["school_proximity"] = f"RBF(300m) of nearest school at {school_d:.0f} m"
        provenance["hospital_proximity"] = f"RBF(500m) of nearest hospital at {hospital_d:.0f} m"
        provenance["landmark_proximity"] = (
            f"RBF(200m) of nearest landmark {any_lm.landmark.name if any_lm else 'n/a'}"
        )
        provenance["waterbody_proximity"] = f"RBF(400m) of nearest water body at {water_d:.0f} m"
        provenance["pathway_proximity"] = (
            f"pathway within {2 * (pathway.landmark.radius_m if pathway else 0)} m: {bool(pathway_prox)}"
        )

        # 3. Exposure (GeoGPT "slope") -----------------------------------------
        traffic_map = {"high": 1.0, "moderate": 0.5, "low": 0.0}
        nearby_result = NearbyIncidentsResult(
            center=point,
            radius_m=self.nearby_radius_m,
            incidents=ctx.nearby_reports,
            total_in_radius=len(ctx.nearby_reports),
            mode="memory",
            basis=["feature-engine input"],
        )
        exposure = reasoning.compute_exposure(
            point, landmarks=self.landmarks, nearby=nearby_result
        )
        features["traffic"] = traffic_map[exposure.traffic_exposure]
        features["junction_density_1km"] = _cap1(exposure.junction_density_1km / 3.0)
        raw["junction_density_per_km2"] = round(exposure.junction_density_1km, 4)
        raw["traffic_exposure_level"] = exposure.traffic_exposure
        provenance["traffic"] = f"traffic exposure {exposure.traffic_exposure} from map reasoning"
        provenance["junction_density_1km"] = (
            f"{exposure.junction_density_1km:.2f} junctions/km2 (landmark count heuristic)"
        )

        # 4. Population proxy (GeoGPT "neighbourhood statistics") ---------------
        pop_landmarks = [
            lm
            for lm in self.landmarks.within(point, radius_m=1_000.0)
            if lm.kind in POPULATION_PROXY_KINDS
        ]
        pop_density = len(pop_landmarks) / (math.pi * 1.0)  # per km^2 in 1 km radius
        features["population_density_proxy"] = round(_cap1(pop_density / 5.0), 4)
        raw["population_proxy_landmarks_1km"] = len(pop_landmarks)
        provenance["population_density_proxy"] = (
            f"{len(pop_landmarks)} commercial/transit landmarks within 1 km "
            "(proxy for resident density; not census data)"
        )

        # 5. Report neighbourhood (GeoGPT "flow accumulation") -----------------
        reports = ctx.nearby_reports
        count = len(reports)
        features["nearby_report_count"] = _cap1(count / 10.0)
        raw["nearby_report_count"] = count
        provenance["nearby_report_count"] = f"{count} report(s) within {self.nearby_radius_m:.0f} m"

        area_km2 = math.pi * (self.nearby_radius_m / 1000.0) ** 2
        density = count / area_km2 if area_km2 > 0 else 0.0
        features["incident_density_1km"] = round(_cap1(density / 10.0), 4)
        raw["incident_density_per_km2"] = round(density, 3)
        provenance["incident_density_1km"] = (
            f"{density:.2f} reports/km2 (neighbourhood report statistics)"
        )

        if reports:
            distances = sorted(r.distance_m for r in reports)
            nearest_d = distances[0]
            mean_d = sum(distances) / len(distances)
            features["nearest_report_distance_sim"] = round(_rbf(nearest_d, 200.0), 4)
            features["mean_report_distance_sim"] = round(_rbf(mean_d, 300.0), 4)
            raw["nearest_report_distance_m"] = round(nearest_d, 1)
            raw["mean_report_distance_m"] = round(mean_d, 1)
            provenance["nearest_report_distance_sim"] = (
                f"RBF(200m) of nearest report at {nearest_d:.0f} m — 'distance between reports'"
            )
            provenance["mean_report_distance_sim"] = (
                f"RBF(300m) of mean report distance {mean_d:.0f} m"
            )
        else:
            features["nearest_report_distance_sim"] = 0.0
            features["mean_report_distance_sim"] = 0.0
            raw["nearest_report_distance_m"] = -1
            raw["mean_report_distance_m"] = -1
            provenance["nearest_report_distance_sim"] = "no nearby reports"
            provenance["mean_report_distance_sim"] = "no nearby reports"

        # 6. Repeated reports + time context (GeoGPT "time series statistics") --
        repeated = sum(int(r.duplicates_seen) for r in reports)
        features["repeated_reports"] = round(_cap1(repeated / 8.0), 4)
        raw["repeated_reports_total"] = repeated
        provenance["repeated_reports"] = (
            f"{repeated} merged report sighting(s) across {count} nearby record(s)"
        )

        times_applied = False
        if reports:
            times = [
                r.reported_at
                for r in reports
                if r.reported_at is not None and r.reported_at <= ctx.submitted_at
            ]
            if times:
                first = min(times)
                hours_since_first = max(0.0, (ctx.submitted_at - first).total_seconds() / 3600.0)
                features["time_since_first_report_norm"] = round(math.tanh(hours_since_first / 72.0), 4)
                raw["time_since_first_report_h"] = round(hours_since_first, 2)
                provenance["time_since_first_report_norm"] = (
                    f"tanh(h/72): {hours_since_first:.1f} h since first nearby report"
                )
                times_applied = True
                if len(times) >= 2:
                    span_h = max((_utc(t) - _utc(first)).total_seconds() for t in times) / 3600.0
                    features["report_time_span_norm"] = round(math.tanh(span_h / 168.0), 4)
                    raw["report_time_span_h"] = round(span_h, 2)
                    provenance["report_time_span_norm"] = f"tanh(h/168): spread {span_h:.1f} h"
        if not times_applied:
            features["time_since_first_report_norm"] = 0.0
            provenance["time_since_first_report_norm"] = "no earlier nearby reports"

        # 7. Temporal of day (local-flow context) --------------------------------
        local = _utc(ctx.submitted_at)
        features["hour_of_day_norm"] = round(local.hour / 24.0, 4)
        features["is_weekend"] = float(local.weekday() >= 5)
        raw["hour_of_day_utc"] = local.hour
        raw["is_weekend"] = int(local.weekday() >= 5)
        provenance["hour_of_day_norm"] = f"UTC hour {local.hour} normalized to [0,1]"
        provenance["is_weekend"] = "1 on Sat/Sun (UTC interpretation)"

        # 8. Category ------------------------------------------------------------
        canon = normalize_category(ctx.category)
        features["category_is_known"] = 1.0 if canon else 0.0
        raw["category_canonical"] = canon or "unknown"
        provenance["category_is_known"] = f"canonical category: {canon or 'unknown'}"
        for cat in CANONICAL_CATEGORIES:
            features[f"category_{cat}"] = 1.0 if canon == cat else 0.0
            provenance[f"category_{cat}"] = f"one-hot of canonical category {cat}"

        basis.append(
            f"geospatial feature vector {SCHEMA_VERSION}: {len(features)} normalized "
            f"features, {len(raw)} raw measurements, {len(provenance)} provenance chains"
        )
        return GeospatialFeatureVector(
            features=features,
            raw=raw,
            provenance=provenance,
            warnings=warnings,
            basis=basis,
        )

    # -- convenience ----------------------------------------------------------

    def compute_for_point(
        self,
        latitude: float,
        longitude: float,
        submitted_at: datetime | None = None,
        category: str | None = None,
        retriever: NearbyRetriever | None = None,
        memory_incidents: list[dict[str, object]] | None = None,
    ) -> GeospatialFeatureVector:
        """One-call: retrieve nearby reports then compute the vector."""
        point = GeoPoint(latitude=latitude, longitude=longitude)
        submitted_at = submitted_at or datetime.now(timezone.utc)
        if retriever is None:
            retriever = NearbyRetriever(executor=None)
        nearby = retriever.retrieve(
            SpatialSearchSpec(center=point, radius_m=self.nearby_radius_m, limit=50),
            memory_incidents=memory_incidents or [],
        )
        return self.compute(
            CivicIncidentContext(
                latitude=latitude,
                longitude=longitude,
                submitted_at=submitted_at,
                category=category,
                nearby_reports=nearby.incidents,
            )
        )


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)