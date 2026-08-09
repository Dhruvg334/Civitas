"""Civitas ML service: `analyze_report` composition (Phase 9).

One typed call that composes the whole before-action ML stack:

    vision -> embeddings -> duplicate -> severity -> priority

`memory_incidents` (known incidents for duplicate comparison) and
`landmarks` (the landmark index) are optional call-time context; the ML
service owns no persistence, per the architecture boundaries. Every
section records what it actually ran in `basis`; missing inputs degrade
sections to `available=False` / `verdict='unknown'` with the reason
recorded — never a guessed number.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypeAlias

from PIL import Image

from civitas_duplicates import (
    ClassicalImageEmbedder,
    DuplicateDetector,
    HashNgramEmbedder,
    ReportLike,
    build_report_embeddings,
)
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
    GeospatialFeatureVector,
)
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import ExposureContext, GeoPoint, SpatialSearchSpec
from civitas_geo.reasoning import compute_exposure
from civitas_geo.retrieval import NearbyRetriever
from civitas_risk import (
    ConsolidatedIncident,
    IncidentVisualEvidence,
    PriorityContext,
    PriorityModel,
    SeverityModel,
    build_incident_features,
    build_priority_features,
)
from civitas_vision.detector import VisualIntelligencePipeline
from civitas_vision.features import extract_features

from civitas_ml.contracts import (
    DuplicateCandidate,
    DuplicateSection,
    EmbeddingSection,
    FactorPoint,
    PrioritySection,
    ReportAnalysis,
    SeveritySection,
    VisionSection,
)

VISION_TO_CATEGORY = {
    "water_leakage": "water leak",
    "pothole_road_damage": "road damage",
    "garbage_overflow": "garbage",
    "broken_streetlight": "streetlight",
    "fallen_tree": "fallen tree",
}

Media: TypeAlias = Image.Image | str | os.PathLike[str]

_VISION = VisualIntelligencePipeline()


def _load_media(media: Media) -> Image.Image:
    if isinstance(media, Image.Image):
        return media
    return Image.open(Path(media))


def _density_records(memory: list[ReportLike]) -> list[dict[str, object]]:
    """The engine's density-record shape, derived from the incident memory."""
    return [
        {
            "incident_id": r.report_id,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "category": r.category,
            "duplicates_seen": 1,
            "reported_at": r.submitted_at,
        }
        for r in memory
    ]


def _geospatial_context(
    latitude: float | None,
    longitude: float | None,
    landmarks: LandmarkIndex | None,
    memory: list[ReportLike],
    timestamp: datetime,
) -> tuple[ExposureContext | None, GeospatialFeatureVector | None, list[str]]:
    """Exposure + geo feature engine for lat/lon + landmarks, else None."""
    if latitude is None or longitude is None:
        return None, None, ["no coordinates supplied; geospatial context absent"]
    if landmarks is None:
        return None, None, ["no landmark index supplied; geospatial context absent"]
    point = GeoPoint(latitude=latitude, longitude=longitude)
    nearby = NearbyRetriever(executor=None).retrieve(
        SpatialSearchSpec(center=point, radius_m=800, limit=10),
        memory_incidents=_density_records(memory),
    )
    exposure = compute_exposure(point, landmarks=landmarks, nearby=nearby)
    engine = GeospatialFeatureEngine(landmarks=landmarks).compute(
        CivicIncidentContext(
            latitude=latitude,
            longitude=longitude,
            submitted_at=timestamp,
            category=None,
            nearby_reports=nearby.incidents,
        )
    )
    basis = ["exposure from landmark index at report point"]
    return exposure, engine, basis


def analyze_report(
    image: Media | None = None,
    video: str | os.PathLike[str] | None = None,
    description: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    timestamp: datetime | None = None,
    *,
    report_id: str = "REPORT-001",
    memory_incidents: list[ReportLike] | None = None,
    landmarks: LandmarkIndex | None = None,
    now: datetime | None = None,
) -> ReportAnalysis:
    """Analyse one citizen report end-to-end.

    Runs the whole before-action stack: vision (image or video), report
    embeddings, duplicate verdict against the supplied incident memory,
    single-report severity and priority. Returns typed stable sections.
    """
    basis: list[str] = ["civitas-ml analyze_report", "composed: vision + embeddings + duplicates + risk"]
    when = timestamp or now or datetime.now(timezone.utc)
    memory = memory_incidents or []

    vision_result = None
    vision_basis: list[str] = []
    if image is not None:
        loaded = _load_media(image)
        vision_result = _VISION.analyze_image(loaded)
        vision_basis = ["analyzed image via VisualIntelligencePipeline"]
    elif video is not None:
        vision_result = _VISION.analyze_video(str(video))
        vision_basis = ["analyzed video via VisualIntelligencePipeline"]
    else:
        vision_basis = ["no media supplied"]

    vision = VisionSection(
        media_usable=vision_result.media_usable if vision_result else False,
        media_rejected_basis=list(vision_result.basis) if vision_result and not vision_result.media_usable else [],
        primary_category=vision_result.primary_category if vision_result else None,
        observable_evidence=list(vision_result.observable_evidence) if vision_result else [],
        basis=vision_basis,
    )

    category = VISION_TO_CATEGORY.get(vision.primary_category or "") if vision.primary_category else None

    text_embedder = HashNgramEmbedder()
    image_embedder = ClassicalImageEmbedder()
    report_embeddings = build_report_embeddings(
        report_id=report_id,
        description=description,
        text_embedder=text_embedder,
        image=image if isinstance(image, Image.Image) else None,
        image_embedder=image_embedder if isinstance(image, Image.Image) else None,
        gps=(latitude, longitude) if latitude is not None and longitude is not None else None,
        submitted_at=when.isoformat(),
        category=category,
        landmark_ids=[],
    )
    embeddings = EmbeddingSection(
        text_embedding=report_embeddings.text_embedding,
        text_dim=len(report_embeddings.text_embedding),
        image_embedding=report_embeddings.image_embedding,
        image_dim=len(report_embeddings.image_embedding) if report_embeddings.image_embedding else None,
        method=report_embeddings.basis[0] if report_embeddings.basis else "text hashing",
        basis=list(report_embeddings.basis),
    )

    duplicate = _duplicate_section(
        report_id=report_id,
        description=description,
        latitude=latitude,
        longitude=longitude,
        timestamp=when,
        category=category,
        image_embedding=report_embeddings.image_embedding,
        memory=memory,
        landmarks=landmarks,
    )

    exposure, geo_engine, geo_basis = _geospatial_context(latitude, longitude, landmarks, memory, when)

    severity = SeveritySection(available=False, basis=["no media and no description supplied"])
    priority = PrioritySection(available=False, basis=["severity unavailable"])
    if vision.primary_category is not None or description:
        incident = ConsolidatedIncident(
            incident_id=report_id,
            category=category or "unclassified",
            visual=IncidentVisualEvidence.from_evidence(
                primary_category=vision.primary_category,
                observed_evidence=vision.observable_evidence,
                water_coverage=(
                    extract_features(_load_media(image))["blue_smooth_share"]
                    if isinstance(image, Image.Image)
                    else 0.0
                ),
            ),
            exposure=exposure,
            report_count=1,
            duration_hours=0.0,
        )
        features = build_incident_features(incident)
        severity_result = SeverityModel().assess(features)
        severity = SeveritySection(
            available=True,
            score=severity_result.score,
            level=severity_result.level,
            factors=[
                FactorPoint(factor=f.factor, points=f.points, evidence=f.evidence)
                for f in severity_result.contributing_factors
            ],
            basis=["single-report severity (not cluster-aware)", *geo_basis],
        )
        if geo_engine is not None:
            priority_context = PriorityContext(
                incident=incident,
                severity_score=severity_result.score,
                population_density_proxy=geo_engine.features["population_density_proxy"],
                nearby_density_norm=geo_engine.features["incident_density_1km"],
                current_time=when,
            )
            priority_result = PriorityModel().assess(build_priority_features(priority_context))
            priority = PrioritySection(
                available=True,
                score=priority_result.score,
                level=priority_result.level,
                reasons=[
                    FactorPoint(factor=r.factor, points=r.points, evidence=r.evidence)
                    for r in priority_result.reasons
                ],
                basis=["priority v2 (10-signal model)", *geo_basis],
            )
        else:
            priority = PrioritySection(available=False, basis=[*geo_basis, "priority needs geospatial context"])

    return ReportAnalysis(
        report_id=report_id,
        vision=vision,
        embeddings=embeddings,
        duplicate=duplicate,
        severity=severity,
        priority=priority,
        basis=basis,
    )


def _duplicate_section(
    report_id: str,
    description: str,
    latitude: float | None,
    longitude: float | None,
    timestamp: datetime,
    category: str | None,
    image_embedding: list[float] | None,
    memory: list[ReportLike],
    landmarks: LandmarkIndex | None,
) -> DuplicateSection:
    if not memory:
        return DuplicateSection(
            mode="no-memory",
            verdict="unknown",
            basis=["no incident memory supplied; duplicate verdict not attempted"],
        )
    if latitude is None or longitude is None:
        return DuplicateSection(
            mode="no-geo",
            verdict="unknown",
            basis=["no coordinates supplied; spatial duplicate comparison not attempted"],
        )
    report = ReportLike(
        report_id=report_id,
        description=description,
        latitude=latitude,
        longitude=longitude,
        submitted_at=timestamp,
        category=category,
        landmark_ids=[],
        image_embedding=image_embedding,
        media_count=1 if image_embedding else 0,
    )
    engine = DuplicateDetector(
        landmark_index=landmarks,
        density_records=_density_records(memory),
    )
    results = [engine.evaluate_pair(report, other) for other in memory]
    results.sort(key=lambda r: r.score, reverse=True)
    candidates = [
        DuplicateCandidate(
            report_id=r.report_b,
            similarity=round(r.score, 4),
            is_duplicate=r.is_duplicate,
            requires_review=r.requires_review,
            reasons=list(r.reasons),
        )
        for r in results
    ]
    best = candidates[0] if candidates else None
    verdict: Literal["new", "duplicate", "unknown"] = "new"
    if best is not None and best.is_duplicate:
        verdict = "duplicate"
    return DuplicateSection(
        mode="full",
        verdict=verdict,
        candidates=candidates[:3],
        best_match=best,
        basis=[f"paired against {len(memory)} memory incident(s)"],
    )