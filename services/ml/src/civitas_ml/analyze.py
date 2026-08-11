"""Civitas ML service: analyse-a-report composition (Phases 9-10).

One typed call that composes the whole before-action ML stack:

    vision -> embeddings -> duplicates -> clustering -> severity -> priority

The module exposes the offline entry point `analyze_report` (call-time
context) plus the reusable section builders that the adapter-driven
pipeline (`civitas_ml.pipeline`) composes with backend-retrieved
context. The ML service owns no persistence and no workflow state.

Every section records what it actually ran in `basis`; missing inputs
degrade sections to `available=False` / `verdict='unknown'` with the
reason recorded — never a guessed number.
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
    ScoredPair,
    build_report_embeddings,
    cluster_reports,
)
from civitas_duplicates.contracts import DuplicateResult
from civitas_duplicates.embeddings import ReportEmbeddings
from civitas_duplicates.geo_features import gps_distance_m
from civitas_duplicates.similarity import ScoringConfig
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
    GeospatialFeatureVector,
)
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import ExposureContext, GeoPoint, SpatialSearchSpec
from civitas_geo.reasoning import compute_exposure
from civitas_geo.retrieval import NearbyRetriever
from civitas_resolution import (
    COVERAGE_GROWTH_CONFLICT_RATIO,
    STANDING_WATER_EVIDENCE_MIN,
    ResolutionModel,
)
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
from civitas_vision.quality import (
    MAX_BLUR_SCORE,
    MAX_LUMINANCE,
    MIN_LUMINANCE,
    MIN_WIDTH_PX,
)

from civitas_ml.contracts import (
    ClusterSection,
    DuplicateCandidate,
    DuplicateSection,
    EmbeddingSection,
    FactorPoint,
    GeospatialSection,
    MediaReference,
    ModelReference,
    PrioritySection,
    ReportAnalysis,
    SeveritySection,
    VisionSection,
)
from civitas_ml.media import resolve_video

VISION_TO_CATEGORY = {
    "water_leakage": "water leak",
    "pothole_road_damage": "road damage",
    "garbage_overflow": "garbage",
    "broken_streetlight": "streetlight",
    "fallen_tree": "fallen tree",
    "other_infrastructure_damage": "wall damage",
    "drainage_damage": "drainage damage",
    "no_incident": "no incident",
    "pest_infestation": "pest infestation",
}

# A classification at or above this probability is treated as confident;
# below it the pipeline flags uncertainty in `basis` instead of pretending.
LOW_VISION_CONFIDENCE = 0.40
# Mean nearest-prototype distance more than 2x the corpus median distance:
# the media sits outside the training manifold -> flag uncertainty, never
# assert a category as fact.
OOD_RATIO_UNCERTAINTY = 2.0

Media: TypeAlias = Image.Image | str | os.PathLike[str]

_VISION = VisualIntelligencePipeline()
_DUPLICATE_CFG = ScoringConfig()
_EMBEDDING_METHOD_VERSION = "civitas-embeddings-v1"
_DUPLICATE_ENGINE_VERSION = "duplicates-engine-v1"
_VISION_MODEL_VERSION = "vision-knn-v1"

# Thresholds documented on the model card; identical to the values the
# underlying models use (imported above where the constant exists).
SEVERITY_BANDS = {"critical_min": 80.0, "high_min": 60.0, "medium_min": 35.0}
PRIORITY_BANDS = {"critical_min": 80.0, "high_min": 60.0, "medium_min": 40.0}


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


# ---------------------------------------------------------------------------
# Section builders (shared by analyze_report and the adapter-driven pipeline)
# ---------------------------------------------------------------------------


def collect_vision_uncertainty(section: VisionSection) -> list[str]:
    """Honest uncertainty notes for a vision section; empty when confident.

    Low confidence under the floor and out-of-distribution media both mean
    the pipeline must record "we are not sure" instead of asserting a
    category as fact.
    """
    notes: list[str] = []
    if (
        section.primary_category is not None
        and section.media_usable
        and section.confidence < LOW_VISION_CONFIDENCE
    ):
        notes.append(
            f"low-confidence classification: confidence {section.confidence:.2f} "
            f"below the {LOW_VISION_CONFIDENCE:.2f} floor"
        )
    if section.ood_ratio is not None and section.ood_ratio >= OOD_RATIO_UNCERTAINTY:
        notes.append(
            f"out-of-distribution media: distance ratio {section.ood_ratio:.2f} "
            f"above the {OOD_RATIO_UNCERTAINTY:.1f} uncertainty floor; "
            "the category is a best-effort guess, not grounded evidence"
        )
    return notes


def build_vision_section(
    image: Image.Image | None,
    *,
    media_kind: Literal["image", "video", "none"] = "none",
    video_path: str | None = None,
    video_frames: list[Image.Image] | None = None,
    video_meta: dict[str, int | float | None] | None = None,
    no_media_note: str = "no media supplied",
    pipeline: VisualIntelligencePipeline | None = None,
) -> tuple[VisionSection, str | None]:
    """Run the vision stack on one resolved image (or pre-decoded video frames)."""
    vision_pipeline = pipeline or _VISION
    vision_result = None
    basis: list[str] = []
    if image is not None:
        vision_result = vision_pipeline.analyze_image(image)
        basis = ["analyzed image via VisualIntelligencePipeline"]
    elif video_path is not None or video_frames is not None:
        vision_result = vision_pipeline.analyze_video(
            video_path or "",
            video_extra_frames=video_frames,
        )
        basis = [
            "analyzed video via VisualIntelligencePipeline",
            f"decoded {len(video_frames or [])} video frame(s) before key-frame selection",
        ]
    else:
        basis = [no_media_note]

    meta = video_meta or {}
    total = meta.get("video_total_frames")
    section = VisionSection(
        media_usable=vision_result.media_usable if vision_result else False,
        media_rejected_basis=list(vision_result.basis) if vision_result and not vision_result.media_usable else [],
        primary_category=vision_result.primary_category if vision_result else None,
        secondary_categories=list(vision_result.secondary_categories) if vision_result else [],
        secondary_label=vision_result.secondary_label if vision_result else None,
        precise_observable_description=(
            vision_result.precise_observable_description if vision_result else ""
        ),
        observable_evidence=list(vision_result.observable_evidence) if vision_result else [],
        confidence=vision_result.confidence if vision_result else 0.0,
        ood_ratio=vision_result.ood_ratio if vision_result else None,
        media_kind=media_kind,
        frames_selected=vision_result.frames_selected if vision_result else 0,
        video_total_frames=int(total) if total is not None else None,
        video_duration_s=meta.get("video_duration_s"),
        video_fps=meta.get("video_fps"),
        basis=basis,
    )
    section.uncertainty.extend(collect_vision_uncertainty(section))
    if section.uncertainty:
        section.basis.extend(section.uncertainty)
    category = VISION_TO_CATEGORY.get(section.primary_category or "") if section.primary_category else None
    return section, category


def build_embedding_section(
    report_id: str,
    description: str,
    image: Image.Image | None,
    category: str | None,
    when: datetime,
    *,
    landmark_ids: list[str] | None = None,
) -> tuple[EmbeddingSection, ReportEmbeddings | None]:
    """Text + image embeddings with centralized dims (never silently mismatched)."""
    try:
        text_embedder = HashNgramEmbedder()
        image_embedder = ClassicalImageEmbedder()
        report_embeddings = build_report_embeddings(
            report_id=report_id,
            description=description,
            text_embedder=text_embedder,
            image=image,
            image_embedder=image_embedder if image is not None else None,
            gps=None,
            submitted_at=when.isoformat(),
            category=category,
            landmark_ids=landmark_ids or [],
        )
    except Exception as exc:  # noqa: BLE001 - embedder failure degrades, never crashes
        return (
            EmbeddingSection(
                available=False,
                failure=f"embedding dependency failed: {exc}",
                text_dim=0,
                method="unavailable",
                basis=["embedding generation unavailable"],
            ),
            None,
        )
    section = EmbeddingSection(
        available=True,
        text_embedding=report_embeddings.text_embedding,
        text_dim=len(report_embeddings.text_embedding),
        method=report_embeddings.basis[0] if report_embeddings.basis else "text hashing",
        image_embedding=report_embeddings.image_embedding,
        image_dim=len(report_embeddings.image_embedding) if report_embeddings.image_embedding else None,
        basis=list(report_embeddings.basis),
    )
    return section, report_embeddings


def evaluate_memory_pairs(
    report: ReportLike,
    memory: list[ReportLike],
    landmarks: LandmarkIndex | None,
    *,
    has_coordinates: bool,
) -> tuple[list[DuplicateResult], DuplicateSection]:
    """Score the report against each memory report (explainable pair results)."""
    if not memory:
        return [], DuplicateSection(
            mode="no-memory",
            verdict="unknown",
            basis=["no incident memory supplied; duplicate verdict not attempted"],
        )
    if not has_coordinates:
        return [], DuplicateSection(
            mode="no-geo",
            verdict="unknown",
            basis=["no coordinates supplied; spatial duplicate comparison not attempted"],
        )
    engine = DuplicateDetector(
        landmark_index=landmarks,
        density_records=_density_records(memory),
        config=_DUPLICATE_CFG,
    )
    results = [engine.evaluate_pair(report, other) for other in memory]
    results.sort(key=lambda r: r.score, reverse=True)
    candidates = [
        DuplicateCandidate(
            report_id=r.report_b,
            similarity=round(r.score, 4),
            is_duplicate=r.is_duplicate,
            requires_review=r.requires_review,
            feature_contributions=dict(r.feature_contributions),
            reasons=list(r.reasons),
        )
        for r in results
    ]
    best = candidates[0] if candidates else None
    verdict: Literal["new", "duplicate", "unknown"] = "new"
    if best is not None and best.is_duplicate:
        verdict = "duplicate"
    return results, DuplicateSection(
        mode="full",
        verdict=verdict,
        candidates=candidates[:3],
        best_match=best,
        basis=[f"paired against {len(memory)} memory incident(s)"],
    )


def build_cluster_section(
    report: ReportLike,
    memory: list[ReportLike],
    pair_results: list[DuplicateResult],
) -> ClusterSection:
    """Conservative, explainable incident clustering over scored pairs.

    Edges only form when the composite score clears the duplicate
    threshold (0.70); geographic proximity alone never merges.
    """
    all_reports = [report, *memory]
    positions = {r.report_id: (r.latitude, r.longitude) for r in all_reports}
    scored: list[ScoredPair] = []
    for result in pair_results:
        next(r for r in all_reports if r.report_id == result.report_b)  # noqa: B018 - existence guard
        scored.append(
            ScoredPair(
                a=result.report_a,
                b=result.report_b,
                score=result.score,
                distance_m=gps_distance_m(
                    positions[result.report_a][0], positions[result.report_a][1],
                    positions[result.report_b][0], positions[result.report_b][1],
                ),
            )
        )
    clusters = cluster_reports(all_reports, scored, cfg=_DUPLICATE_CFG, cluster_id_start=1000)
    for incident in clusters:
        if report.report_id in incident.report_ids:
            return ClusterSection(
                available=True,
                cluster_id=incident.cluster_id,
                member_count=incident.member_count,
                member_report_ids=list(incident.report_ids),
                mean_pairwise_score=incident.mean_pairwise_score,
                span_m=incident.span_m,
                verdict="merged" if incident.member_count > 1 else "isolated",
                basis=list(incident.basis),
            )
    return ClusterSection(
        available=False,
        verdict="unknown",
        basis=["report not placed in any incident cluster (no scored pairs)"],
    )


def build_geo_section(
    latitude: float | None,
    longitude: float | None,
    landmarks: LandmarkIndex | None,
    memory: list[ReportLike],
    when: datetime,
) -> tuple[ExposureContext | None, GeospatialFeatureVector | None, GeospatialSection]:
    """Exposure + geo feature engine for lat/lon + landmarks, else absent."""
    if latitude is None or longitude is None:
        return None, None, GeospatialSection(
            available=False, basis=["no coordinates supplied; geospatial context absent"]
        )
    if landmarks is None:
        return None, None, GeospatialSection(
            available=False, basis=["no landmark index supplied; geospatial context absent"]
        )
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
            submitted_at=when,
            category=None,
            nearby_reports=nearby.incidents,
        )
    )
    section = GeospatialSection(
        available=True,
        population_density_proxy=engine.features.get("population_density_proxy"),
        incident_density_1km=engine.features.get("incident_density_1km"),
        nearby_landmarks=[
            f"{kind} @ {distance:.0f} m"
            for kind, distance in (
                ("school", exposure.nearest_school_m),
                ("hospital", exposure.nearest_hospital_m),
                ("waterbody", exposure.nearest_waterbody_m),
            )
            if distance is not None
        ],
        basis=["exposure from landmark index at report point"],
    )
    return exposure, engine, section


def build_scoring_sections(
    *,
    category: str | None,
    vision_primary: str | None,
    description: str,
    evidence: list[str],
    image: Image.Image | None,
    exposure: ExposureContext | None,
    geo_engine: GeospatialFeatureVector | None,
    geo_basis: list[str],
    when: datetime,
    report_count: int = 1,
    duration_hours: float = 0.0,
    cluster_note: str | None = None,
) -> tuple[SeveritySection, PrioritySection, SeverityModel, PriorityModel]:
    """Severity (how serious) and priority (how urgent) as SEPARATE outputs.

    Both consume the same contextual features but answer different
    questions; they are never collapsed into one risk score.
    """
    severity = SeveritySection(available=False, basis=["no media and no description supplied"])
    priority = PrioritySection(available=False, basis=["severity unavailable"])
    if vision_primary is None and not description:
        return severity, priority, SeverityModel(), PriorityModel()
    incident = ConsolidatedIncident(
        incident_id="incident",
        category=category or "unclassified",
        visual=IncidentVisualEvidence.from_evidence(
            primary_category=vision_primary,
            observed_evidence=evidence,
            water_coverage=(
                extract_features(image)["blue_smooth_share"] if image is not None else 0.0
            ),
        ),
        exposure=exposure,
        report_count=max(report_count, 1),
        duration_hours=max(duration_hours, 0.0),
    )
    severity_model = SeverityModel()
    severity_result = severity_model.assess(build_incident_features(incident))
    severity = SeveritySection(
        available=True,
        score=severity_result.score,
        level=severity_result.level,
        factors=[
            FactorPoint(factor=f.factor, points=f.points, evidence=f.evidence)
            for f in severity_result.contributing_factors
        ],
        basis=[
            cluster_note or f"severity over {report_count} report(s)",
            *geo_basis,
        ],
    )
    if geo_engine is not None:
        priority_model = PriorityModel()
        priority_result = priority_model.assess(
            build_priority_features(
                PriorityContext(
                    incident=incident,
                    severity_score=severity_result.score,
                    population_density_proxy=geo_engine.features["population_density_proxy"],
                    nearby_density_norm=geo_engine.features["incident_density_1km"],
                    current_time=when,
                )
            )
        )
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
        return severity, priority, severity_model, priority_model
    priority = PrioritySection(available=False, basis=[*geo_basis, "priority needs geospatial context"])
    return severity, priority, severity_model, PriorityModel()


def collect_models(
    severity_model: SeverityModel,
    priority_model: PriorityModel,
    *,
    resolution_model: ResolutionModel | None = None,
    text_dim: int = 0,
    image_dim: int | None = None,
    vision_model_version: str | None = None,
) -> list[ModelReference]:
    """The metadata block: every model that ran, with versions + thresholds."""
    models: list[ModelReference] = [
        ModelReference(
            component="vision",
            model_version=vision_model_version or _VISION_MODEL_VERSION,
            thresholds={
                "blur_max": MAX_BLUR_SCORE,
                "min_luminance": MIN_LUMINANCE,
                "max_luminance": MAX_LUMINANCE,
                "min_width_px": float(MIN_WIDTH_PX),
                "low_confidence_floor": LOW_VISION_CONFIDENCE,
            },
            note=(
                f"{vision_model_version or _VISION_MODEL_VERSION}; five frozen MVP categories only"
            ),
        ),
        ModelReference(
            component="embeddings",
            model_version=_EMBEDDING_METHOD_VERSION,
            thresholds={"text_dim": float(text_dim), "image_dim": float(image_dim or 0)},
        ),
        ModelReference(
            component="duplicates",
            model_version=_DUPLICATE_ENGINE_VERSION,
            thresholds={
                "duplicate_threshold": _DUPLICATE_CFG.duplicate_threshold,
                "max_reasonable_distance_m": _DUPLICATE_CFG.max_reasonable_distance_m,
                "max_reasonable_delta_h": _DUPLICATE_CFG.max_reasonable_delta_h,
            },
        ),
        ModelReference(
            component="severity",
            model_version=severity_model.model_version,
            thresholds=dict(SEVERITY_BANDS),
            note="bands documented from severity-model-v1 assess",
        ),
        ModelReference(
            component="priority",
            model_version=priority_model.model_version,
            thresholds=dict(PRIORITY_BANDS),
            note="bands documented from priority-model-v2 assess",
        ),
    ]
    if resolution_model is not None:
        models.append(
            ModelReference(
                component="resolution",
                model_version=resolution_model.model_version,
                thresholds={
                    "standing_water_evidence_min": STANDING_WATER_EVIDENCE_MIN,
                    "coverage_growth_conflict_ratio": COVERAGE_GROWTH_CONFLICT_RATIO,
                },
            )
        )
    return models


# ---------------------------------------------------------------------------
# Offline entry point (call-time context; the pipeline adds backend retrieval)
# ---------------------------------------------------------------------------


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
    vision_pipeline: VisualIntelligencePipeline | None = None,
) -> ReportAnalysis:
    """Analyse one citizen report end-to-end with call-time context.

    Runs the whole before-action stack: vision (image or video), report
    embeddings, duplicate verdict + clustering against the supplied
    incident memory, and separate severity + priority outputs.
    """
    basis: list[str] = ["civitas-ml analyze_report", "composed: vision + embeddings + duplicates + risk"]
    when = timestamp or now or datetime.now(timezone.utc)
    memory = memory_incidents or []

    loaded: Image.Image | None = None
    video_path: str | None = None
    video_frames: list[Image.Image] | None = None
    video_meta: dict[str, int | float | None] | None = None
    media_kind: Literal["image", "video", "none"] = "none"
    media_rejections: list[str] = []
    if image is not None:
        loaded = _load_media(image)
        media_kind = "image"
    elif video is not None:
        video_path = str(video)
        media_kind = "video"
        resolved = resolve_video(MediaReference(local_path=video_path, kind="video"))
        if resolved.frames is None:
            media_rejections.append(
                f"video could not be resolved ({resolved.error_code}): {resolved.error_note}"
            )
        else:
            video_frames = list(resolved.frames)
            video_meta = {
                "video_total_frames": resolved.total_frames,
                "video_duration_s": resolved.duration_s,
                "video_fps": resolved.fps,
            }

    vision, category = build_vision_section(
        loaded,
        media_kind=media_kind,
        video_path=video_path if video_frames is not None else None,
        video_frames=video_frames,
        video_meta=video_meta,
        pipeline=vision_pipeline,
    )
    if media_rejections:
        vision.media_rejected_basis.extend(media_rejections)
        vision.basis.extend(media_rejections)

    # The model version reported on the contract: whichever classifier the
    # selected pipeline actually runs (k-NN default or the real-media CLIP).
    try:
        used_pipeline = vision_pipeline if vision_pipeline is not None else _VISION
        vision_model_version = used_pipeline.classifier.model_version  # type: ignore[attr-defined]
    except AttributeError:
        vision_model_version = _VISION_MODEL_VERSION

    embeddings, report_embeddings = build_embedding_section(
        report_id, description, loaded, category, when
    )

    report_like = ReportLike(
        report_id=report_id,
        description=description,
        latitude=latitude if latitude is not None else 0.0,
        longitude=longitude if longitude is not None else 0.0,
        submitted_at=when,
        category=category,
        landmark_ids=[],
        image_embedding=report_embeddings.image_embedding if report_embeddings else None,
        media_count=1 if loaded is not None else 0,
    )
    pair_results, duplicate = evaluate_memory_pairs(
        report_like, memory, landmarks,
        has_coordinates=latitude is not None and longitude is not None,
    )
    cluster = build_cluster_section(report_like, memory, pair_results)

    exposure, geo_engine, geo_section = build_geo_section(latitude, longitude, landmarks, memory, when)

    severity, priority, severity_model, priority_model = build_scoring_sections(
        category=category,
        vision_primary=vision.primary_category,
        description=description,
        evidence=vision.observable_evidence,
        image=loaded,
        exposure=exposure,
        geo_engine=geo_engine,
        geo_basis=geo_section.basis,
        when=when,
        report_count=1,
        duration_hours=0.0,
        cluster_note="single-report severity (not cluster-aware)",
    )

    models = collect_models(
        severity_model,
        priority_model,
        text_dim=embeddings.text_dim,
        image_dim=embeddings.image_dim,
        vision_model_version=vision_model_version,
    )

    return ReportAnalysis(
        report_id=report_id,
        vision=vision,
        embeddings=embeddings,
        duplicate=duplicate,
        cluster=cluster,
        geospatial=geo_section,
        severity=severity,
        priority=priority,
        models=models,
        basis=basis,
    )


def _cluster_duration_hours(when: datetime, report: ReportLike) -> float:
    """Hours between `when` and the report's submitted time (>= 0).

    The adapter-driven pipeline passes the cluster's earliest report time;
    the offline path only knows this report, so the duration is zero.
    """
    return max(0.0, (when - report.submitted_at).total_seconds() / 3600.0)


__all__ = [
    "LOW_VISION_CONFIDENCE",
    "VISION_TO_CATEGORY",
    "analyze_report",
    "build_cluster_section",
    "build_embedding_section",
    "build_geo_section",
    "build_scoring_sections",
    "build_vision_section",
    "collect_models",
    "evaluate_memory_pairs",
]