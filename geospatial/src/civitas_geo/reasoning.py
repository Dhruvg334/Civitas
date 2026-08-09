"""Map-based reasoning: spatial context that feeds severity and priority.

Consumes observable geography (landmarks, roads, water bodies) plus retrieved
incident context and produces an ExposureContext with only labelled sources
and explicit inference. No signal here is presented as ground truth.
"""

from __future__ import annotations

from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import ExposureContext, GeoPoint, NearbyIncidentsResult, SpatialSearchSpec
from civitas_geo.retrieval import NearbyRetriever

JUNCTION_DENSITY_RADIUS_M = 1_000.0
EXPOSURE_KINDS = ("school", "hospital", "waterbody", "pathway")


def compute_exposure(
    point: GeoPoint,
    landmarks: LandmarkIndex | None = None,
    nearby: NearbyIncidentsResult | None = None,
    roads: list[dict[str, object]] | None = None,
) -> ExposureContext:
    """Build exposure context from landmark geography and retrieved incidents.

    roads: optional list of {"type": "primary"|"secondary"|"residential"|..., "distance_m": n}
    provided by the spatial index when available.
    """
    lm = landmarks or LandmarkIndex()
    sources: list[str] = []
    inference: list[str] = []

    nearest_school = lm.nearest_by_kind(point, "school")
    nearest_hospital = lm.nearest_by_kind(point, "hospital")
    nearest_water = lm.nearest_by_kind(point, "waterbody")
    pathway = lm.nearest_by_kind(point, "pathway")

    junctions = lm.within(point, kind="junction", radius_m=JUNCTION_DENSITY_RADIUS_M)
    density = len(junctions) / (3.14159265 * (JUNCTION_DENSITY_RADIUS_M / 1000.0) ** 2)

    if nearest_school is not None:
        sources.append(f"landmark:{nearest_school.landmark.name}")
    if nearest_hospital is not None:
        sources.append(f"landmark:{nearest_hospital.landmark.name}")
    if nearest_water is not None:
        sources.append(f"landmark:{nearest_water.landmark.name}")
    if pathway is not None:
        sources.append(f"landmark:{pathway.landmark.name}")

    traffic_exposure = "moderate"
    if roads:
        road_types = [str(r.get("type", "")) for r in roads]
        if any(t in road_types for t in ("primary", "trunk", "highway")):
            traffic_exposure = "high"
            sources.append("road:primary-class proximity")
        elif density > 2.0:
            inference.append("junction density heuristic: high")
            traffic_exposure = "high"
    elif density > 2.0:
        traffic_exposure = "high"
        inference.append("junction density heuristic: high")
    elif density < 0.5:
        traffic_exposure = "low"
        inference.append("junction density heuristic: low")

    if nearby is not None and nearby.incidents:
        inference.append(
            f"{nearby.total_in_radius} nearby incident record(s) suggest repeated "
            "activity in this area (retrieved, not confirmed)."
        )

    return ExposureContext(
        nearest_school_m=nearest_school.distance_m if nearest_school else None,
        nearest_hospital_m=nearest_hospital.distance_m if nearest_hospital else None,
        junction_density_1km=round(density, 3),
        nearest_waterbody_m=nearest_water.distance_m if nearest_water else None,
        pathway_proximity=pathway is not None and pathway.distance_m <= pathway.landmark.radius_m * 2,
        traffic_exposure=traffic_exposure,  # type: ignore[arg-type]
        sources=sources,
        inference=inference,
    )


def enrich_incident_context(
    point: GeoPoint,
    retriever: NearbyRetriever,
    spec: SpatialSearchSpec,
    landmarks: LandmarkIndex | None = None,
) -> ExposureContext:
    """One-call enrichment: nearby incidents + map exposure for an incident."""
    nearby = retriever.retrieve(spec)
    return compute_exposure(point, landmarks=landmarks, nearby=nearby)