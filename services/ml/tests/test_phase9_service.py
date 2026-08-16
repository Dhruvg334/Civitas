"""Phase 9 tests: the unified Civitas ML service.

`analyze_report` composes vision, embeddings, duplicate, severity and
priority into one typed, stable output; `verify_resolution` does the
same for the after-action check with a computed confidence. Tests cover
normal (full report with media + memory + landmark context), boundary
(missing media / coordinates / memory) and failure (blurry media)
behaviour, mirroring the demo scenario values where they apply.
"""

from datetime import datetime, timedelta, timezone

from civitas_duplicates import ClassicalImageEmbedder, ReportLike
from civitas_geo.landmarks import LandmarkIndex
from civitas_ml import (
    analyze_report,
    verify_resolution,
)
from civitas_vision.benchmark import gaussian_blur, make_image

T0 = datetime(2026, 3, 1, 10, 30, tzinfo=timezone.utc)
NOON = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)

_IMAGE_EMBEDDER = ClassicalImageEmbedder()


def _memory() -> list[ReportLike]:
    return [
        ReportLike(
            report_id="R2",
            description="flooding on the road in front of sunrise school, water across the footpath",
            latitude=28.6140, longitude=77.2091,
            submitted_at=T0 + timedelta(minutes=30),
            category="flooding",
            image_embedding=_IMAGE_EMBEDDER.embed_image(make_image("water_leakage", 7102)).vector,
            media_count=1,
        ),
        ReportLike(
            report_id="R3",
            description="road surface breaking up after the water, deep cracks near the school",
            latitude=28.6142, longitude=77.2092,
            submitted_at=T0 + timedelta(minutes=75),
            category="road damage",
            image_embedding=_IMAGE_EMBEDDER.embed_image(make_image("pothole_road_damage", 7103)).vector,
            media_count=1,
        ),
        ReportLike(
            report_id="inc-9",
            description="streetlight dark near civic centre metro",
            latitude=28.6190, longitude=77.2165,
            submitted_at=T0 + timedelta(hours=2),
            category="streetlight",
            image_embedding=_IMAGE_EMBEDDER.embed_image(make_image("broken_streetlight", 7200)).vector,
            media_count=1,
        ),
    ]


class TestAnalyzeReport:
    def test_description_only_degrades_gracefully(self):
        analysis = analyze_report(description="water leaking near sunrise school", report_id="Q1")
        assert analysis.report_id == "Q1"
        assert analysis.vision.media_usable is False
        assert "no media supplied" in analysis.vision.basis
        assert analysis.embeddings.text_dim > 0
        assert analysis.embeddings.image_embedding is None
        assert analysis.duplicate.mode == "no-memory"
        assert analysis.duplicate.verdict == "unknown"
        assert analysis.severity.available is True
        assert analysis.priority.available is False

    def test_no_coordinates_skips_spatial_duplicate_and_priority(self):
        analysis = analyze_report(
            image=make_image("water_leakage", 7101, "flow"),
            description="water leaking from the main pipe near sunrise school gate",
            timestamp=T0,
            report_id="R-NOGEO",
            memory_incidents=_memory(),
            landmarks=LandmarkIndex(),
            now=NOON,
        )
        assert analysis.duplicate.mode == "no-geo"
        assert analysis.duplicate.verdict == "unknown"
        assert analysis.severity.available is True
        assert analysis.priority.available is False

    def test_full_pipeline_finds_duplicate_and_scores(self):
        analysis = analyze_report(
            image=make_image("water_leakage", 7101, "flow"),
            description="water leaking from the main pipe near sunrise school gate, road is wet",
            latitude=28.6139, longitude=77.2090,
            timestamp=T0,
            report_id="R1-new",
            memory_incidents=_memory(),
            landmarks=LandmarkIndex(),
            now=NOON,
        )
        assert analysis.vision.media_usable is True
        assert analysis.vision.primary_category == "water_leakage"
        assert "water flowing across road" in analysis.vision.observable_evidence
        assert analysis.embeddings.image_dim is not None
        assert analysis.duplicate.mode == "full"
        assert analysis.duplicate.verdict == "duplicate"
        assert analysis.duplicate.best_match is not None
        assert analysis.duplicate.best_match.report_id == "R2"
        assert analysis.duplicate.best_match.is_duplicate is True
        assert analysis.severity.available is True
        assert analysis.severity.score == 74  # single-report pins (no cluster bonus)
        assert analysis.severity.level == "high"
        factors = {f.factor for f in analysis.severity.factors}
        assert "near school" in factors and "active road flooding" in factors
        assert analysis.priority.available is True
        assert analysis.priority.score == 56  # single-report pins (no repeated-report bonus)
        assert analysis.priority.level == "medium"

    def test_duplicate_candidates_carries_review_flags(self):
        analysis = analyze_report(
            image=make_image("water_leakage", 7101, "flow"),
            description="water leaking from the main pipe near sunrise school gate, road is wet",
            latitude=28.6139, longitude=77.2090,
            timestamp=T0,
            report_id="R1-new",
            memory_incidents=_memory(),
            now=NOON,
        )
        assert analysis.duplicate.best_match is not None
        for candidate in analysis.duplicate.candidates:
            assert 0.0 <= candidate.similarity <= 1.0
            assert isinstance(candidate.requires_review, bool)

    def test_deterministic(self):
        kwargs = dict(
            image=make_image("water_leakage", 7101, "flow"),
            description="water leaking near sunrise school",
            latitude=28.6139, longitude=77.2090,
            timestamp=T0,
            report_id="R1-new",
            memory_incidents=_memory(),
            landmarks=LandmarkIndex(),
            now=NOON,
        )
        assert analyze_report(**kwargs) == analyze_report(**kwargs)


class TestVerifyResolution:
    def test_partial_story_with_confidence(self):
        verification = verify_resolution(
            make_image("water_leakage", 7101, "flow"),
            make_image("water_leakage", 7101, "default"),
            incident_id="CL-018",
        )
        assert verification.status == "partial"
        assert verification.label == "PARTIALLY RESOLVED"
        assert verification.confidence == 0.40
        assert verification.resolved_signals == 1
        assert verification.total_signals == 2
        assert any("no active water flow" in line for line in verification.evidence)
        assert any("standing water remains" in line for line in verification.evidence)
        assert verification.model_version == "resolution-model-v1"

    def test_dry_road_resolved(self):
        verification = verify_resolution(
            make_image("water_leakage", 7101, "flow"),
            make_image("water_leakage", 7101, "dry"),
            incident_id="CL-018",
        )
        assert verification.status == "resolved"
        assert verification.confidence == 0.63
        assert verification.resolved_signals == 2

    def test_blurry_photo_unverifiable(self):
        verification = verify_resolution(
            make_image("water_leakage", 7101, "flow"),
            gaussian_blur(make_image("water_leakage", 7101, "default"), radius=4),
            incident_id="CL-018",
        )
        assert verification.status == "unverifiable"
        assert verification.confidence == 0.0
        assert any("quality gate" in line or "rejected" in line for line in verification.evidence)

    def test_contract_bounds(self):
        verification = verify_resolution(
            make_image("water_leakage", 7101, "flow"),
            make_image("water_leakage", 7101, "default"),
            incident_id="CL-018",
        )
        assert verification.status in {"resolved", "partial", "unverifiable", "conflicting"}
        assert 0.0 <= verification.confidence <= 1.0
        assert verification.incident_id == "CL-018"
        assert verification.evidence

    def test_deterministic(self):
        before = make_image("water_leakage", 7101, "flow")
        after = make_image("water_leakage", 7101, "default")
        first = verify_resolution(before, after, incident_id="CL-018")
        second = verify_resolution(before, after, incident_id="CL-018")
        assert first.model_dump(exclude={"trace_id"}) == second.model_dump(exclude={"trace_id"})