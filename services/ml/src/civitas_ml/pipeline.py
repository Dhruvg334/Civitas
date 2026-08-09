"""The single Phase 10 ML integration entry point.

`run_report` drives the whole Member 2 pipeline for one citizen report:

    media validation -> vision -> embeddings -> backend retrieval
      -> duplicate scoring -> incident clustering -> geospatial features
      -> severity -> priority -> structured ReportAnalysis

`run_resolution` drives the after-action check the same way. Both
retrieve all *backend-owned* data through the `BackendAdapter` interface
(mock now, Utkarsh's real API later), so switching backends is a
configuration change, never an ML rewrite.

Boundaries honoured here:
- ML produces signals (categories, scores, verdicts with evidence) and
  never approves work orders, changes workflow state, closes/reopens
  incidents or performs policy reasoning — those belong to Dhruv/Utkarsh.
- Hard backend/contract failures raise structured `MLServiceError`s;
  everything else degrades to uncertainty recorded in `basis`.
"""

from __future__ import annotations

import uuid
from typing import Literal
from datetime import datetime, timezone

from PIL import Image

from civitas_duplicates import ClassicalImageEmbedder, ReportLike
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import Landmark
from civitas_resolution import (
    COVERAGE_GROWTH_CONFLICT_RATIO,
    STANDING_WATER_EVIDENCE_MIN,
    ResolutionEvidence,
    ResolutionModel,
    outcome_label,
)
from civitas_vision.detector import VisualIntelligencePipeline

from civitas_ml.adapters.base import BackendAdapter
from civitas_ml.analyze import (
    build_cluster_section,
    build_embedding_section,
    build_geo_section,
    build_scoring_sections,
    build_vision_section,
    collect_models,
    evaluate_memory_pairs,
)
from civitas_ml.config import get_backend
from civitas_ml.contracts import (
    CandidateReport,
    ClusterSection,
    FactorPoint,
    ModelReference,
    NearbyCandidatesRequest,
    ReportAnalysis,
    ReportInput,
    ResolutionInput,
    ResolutionVerification,
)
from civitas_ml.errors import CODE_MEDIA_INVALID_KIND
from civitas_ml.media import resolve_media

_IMAGE_EMBEDDER = ClassicalImageEmbedder()
_VISION = VisualIntelligencePipeline()


def _trace() -> str:
    return uuid.uuid4().hex


# ---------------------------------------------------------------------------
# Backend context -> engine inputs (no backend logic ever reaches the models)
# ---------------------------------------------------------------------------


def _candidate_embedding(
    candidate: CandidateReport, backend: BackendAdapter
) -> tuple[list[float] | None, str]:
    """Embed a candidate's first image locally (bytes come from the backend)."""
    images = [r for r in candidate.media_references if r.kind == "image"]
    if not images:
        return None, f"{candidate.report_id}: no image media; text-only comparison"
    resolved = resolve_media(images[0], backend)
    if resolved.image is None:
        return None, f"{candidate.report_id}: candidate image unavailable ({resolved.error_code})"
    try:
        return _IMAGE_EMBEDDER.embed_image(resolved.image).vector, f"{candidate.report_id}: candidate image embedded"
    except Exception as exc:  # noqa: BLE001 - one candidate's embedding failure degrades that candidate only
        return None, f"{candidate.report_id}: candidate embedding failed ({exc})"


def _memory_from_candidates(
    candidates: list[CandidateReport], backend: BackendAdapter
) -> tuple[list[ReportLike], list[str]]:
    memory: list[ReportLike] = []
    notes: list[str] = []
    for candidate in candidates:
        image_embedding, note = _candidate_embedding(candidate, backend)
        notes.append(note)
        memory.append(
            ReportLike(
                report_id=candidate.report_id,
                description=candidate.description,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                submitted_at=candidate.submitted_at,
                category=candidate.category,
                landmark_ids=list(candidate.landmark_ids),
                image_embedding=image_embedding,
                media_count=len([r for r in candidate.media_references if r.kind == "image"]),
            )
        )
    return memory, notes


def _landmark_index(backend: BackendAdapter) -> tuple[LandmarkIndex, list[str]]:
    landmark_set = backend.fetch_landmarks()
    index = LandmarkIndex(
        landmarks=[
            Landmark(
                landmark_id=lm.landmark_id,
                name=lm.name,
                kind=lm.kind,
                latitude=lm.latitude,
                longitude=lm.longitude,
                radius_m=lm.radius_m,
            )
            for lm in landmark_set.landmarks
        ]
    )
    return index, [f"landmarks via backend ({len(landmark_set.landmarks)} entries)"]


# ---------------------------------------------------------------------------
# The report pipeline
# ---------------------------------------------------------------------------


def run_report(
    record: ReportInput,
    backend: BackendAdapter | None = None,
) -> ReportAnalysis:
    """Analyse one report end-to-end through the adapter-driven pipeline."""
    trace_id = record.trace_id or _trace()
    backend = backend or get_backend()
    basis: list[str] = [
        "civitas-ml run_report",
        "composed: media -> vision -> embeddings -> backend retrieval -> duplicates -> cluster -> geo -> severity -> priority",
    ]
    when = record.submitted_at or datetime.now(timezone.utc)

    primary_image, media_errors, media_kind, video_path = _resolve_media(record, backend)
    vision, category = build_vision_section(
        primary_image,
        media_kind=media_kind,
        video_path=video_path,
        no_media_note="no media supplied",
    )
    if media_errors:
        vision.basis.extend(media_errors)
        vision.media_rejected_basis.extend(media_errors)

    embeddings, report_embeddings = build_embedding_section(
        record.report_id, record.description, primary_image, category, when
    )

    candidates_response = None
    if record.latitude is not None and record.longitude is not None:
        candidates_response = backend.fetch_nearby_candidates(
            NearbyCandidatesRequest(
                report_id=record.report_id,
                latitude=record.latitude,
                longitude=record.longitude,
                submitted_at=when,
                category=record.citizen_category or category,
                radius_m=record.retrieval_radius_m,
                time_window_h=record.retrieval_window_h,
            )
        )
    memory, register_notes = (
        _memory_from_candidates(candidates_response.candidates, backend) if candidates_response else ([], [])
    )
    landmark_index, landmark_notes = _landmark_index(backend)

    report_like = ReportLike(
        report_id=record.report_id,
        description=record.description,
        latitude=record.latitude if record.latitude is not None else 0.0,
        longitude=record.longitude if record.longitude is not None else 0.0,
        submitted_at=when,
        category=category,
        landmark_ids=[],
        image_embedding=report_embeddings.image_embedding if report_embeddings else None,
        media_count=1 if primary_image is not None else 0,
    )
    pair_results, duplicate = evaluate_memory_pairs(
        report_like, memory, landmark_index,
        has_coordinates=record.latitude is not None and record.longitude is not None,
    )
    cluster = build_cluster_section(report_like, memory, pair_results)

    exposure, geo_engine, geo_section = build_geo_section(
        record.latitude, record.longitude, landmark_index, memory, when
    )

    if duplicate.mode == "no-memory":
        duplicate.basis.append("no candidates retrieved from the backend within the retrieval window")

    report_count, duration_hours, cluster_note = _cluster_context(
        when, record, report_like, memory, cluster
    )
    severity, priority, severity_model, priority_model = build_scoring_sections(
        category=category,
        vision_primary=vision.primary_category,
        description=record.description,
        evidence=vision.observable_evidence,
        image=primary_image,
        exposure=exposure,
        geo_engine=geo_engine,
        geo_basis=geo_section.basis,
        when=when,
        report_count=report_count,
        duration_hours=duration_hours,
        cluster_note=cluster_note,
    )

    models = collect_models(
        severity_model, priority_model,
        text_dim=embeddings.text_dim, image_dim=embeddings.image_dim,
    )
    return ReportAnalysis(
        report_id=record.report_id,
        trace_id=trace_id,
        vision=vision,
        embeddings=embeddings,
        duplicate=duplicate,
        cluster=cluster,
        geospatial=geo_section,
        severity=severity,
        priority=priority,
        models=models,
        basis=[
            *basis,
            *(candidates_response.basis if candidates_response else []),
            *landmark_notes,
            *register_notes,
        ],
    )


def _resolve_media(
    record: ReportInput, backend: BackendAdapter
) -> tuple[Image.Image | None, list[str], Literal["image", "video", "none"], str | None]:
    """Resolve the report's media: first usable image, or a local video path."""
    errors: list[str] = []
    primary: Image.Image | None = None
    for ref in record.media:
        if primary is not None:
            break
        if ref.kind == "image":
            resolved = resolve_media(ref, backend)
            if resolved.image is not None:
                primary = resolved.image
            elif resolved.error_code:
                errors.append(
                    f"{ref.media_id or ref.local_path}: {resolved.error_note or resolved.error_code}"
                )
    video_path: str | None = None
    for ref in record.media:
        if ref.kind == "video":
            if ref.local_path:
                if video_path is None:
                    video_path = ref.local_path
            else:
                errors.append(
                    f"{ref.media_id}: backend video bytes are not supported yet "
                    f"(code {CODE_MEDIA_INVALID_KIND}); use a local video path"
                )
    if primary is not None:
        return primary, errors, "image", None
    if video_path is not None:
        return None, errors, "video", video_path
    return None, errors, "none", None


def _cluster_context(
    when: datetime,
    record: ReportInput,
    report: ReportLike,
    memory: list[ReportLike],
    cluster: ClusterSection,
) -> tuple[int, float, str]:
    merged = cluster.verdict == "merged"
    count = cluster.member_count if merged else 1
    if merged:
        members = [report, *memory]
        earliest = min(r.submitted_at for r in members)
        duration = max(0.0, (when - earliest).total_seconds() / 3600.0)
    else:
        duration = 0.0
    note = (
        f"severity over incident cluster ({count} report(s), conservative merge)"
        if merged
        else "single-report severity (not cluster-aware)"
    )
    return count, duration, note


# ---------------------------------------------------------------------------
# Resolution pipeline
# ---------------------------------------------------------------------------


def run_resolution(
    record: ResolutionInput,
    backend: BackendAdapter | None = None,
) -> ResolutionVerification:
    """Verify BEFORE vs AFTER media: resolved / partial / conflicting / unverifiable."""
    trace_id = record.trace_id or _trace()
    backend = backend or get_backend()
    basis: list[str] = ["civitas-ml run_resolution", "before/after vision + resolution model"]

    before = resolve_media(record.before, backend)
    after = resolve_media(record.after, backend)
    if before.image is None or after.image is None:
        failed = before if before.image is None else after
        note = failed.error_note or "media could not be resolved"
        return ResolutionVerification(
            incident_id=record.incident_id,
            trace_id=trace_id,
            status="unverifiable",
            label=outcome_label("unverifiable"),
            confidence=0.0,
            resolved_signals=0,
            total_signals=0,
            evidence=[f"media unavailable: {note}"],
            models=[_resolution_model_ref()],
            model_version=ResolutionModel().model_version,
            basis=[*basis, f"media resolution failed: {note}"],
        )

    before_result = _VISION.analyze_image(before.image)
    after_result = _VISION.analyze_image(after.image)
    before_evidence = ResolutionEvidence.from_vision(
        record.incident_id, "before", record.before_source, before_result,
        water_coverage=_water_coverage(before.image),
    )
    after_evidence = ResolutionEvidence.from_vision(
        record.incident_id, "after", record.after_source, after_result,
        water_coverage=_water_coverage(after.image),
    )
    resolution_model = ResolutionModel()
    verdict = resolution_model.assess(before_evidence, after_evidence)
    return ResolutionVerification(
        incident_id=record.incident_id,
        trace_id=trace_id,
        status=verdict.outcome,
        label=outcome_label(verdict.outcome),
        confidence=verdict.confidence,
        resolved_signals=verdict.resolved_signals,
        total_signals=verdict.total_signals,
        evidence=[f"{r.factor}: {r.status} — {r.evidence}" for r in verdict.reasons],
        reasons=[FactorPoint(factor=r.factor, points=0, evidence=r.evidence) for r in verdict.reasons],
        models=[_resolution_model_ref()],
        model_version=resolution_model.model_version,
        basis=[*basis, *verdict.basis],
    )


def _resolution_model_ref() -> ModelReference:
    return ModelReference(
        component="resolution",
        model_version=ResolutionModel().model_version,
        thresholds={
            "standing_water_evidence_min": STANDING_WATER_EVIDENCE_MIN,
            "coverage_growth_conflict_ratio": COVERAGE_GROWTH_CONFLICT_RATIO,
        },
    )


def _water_coverage(image: Image.Image) -> float:
    from civitas_vision.features import extract_features

    return extract_features(image)["blue_smooth_share"]


__all__ = ["run_report", "run_resolution"]