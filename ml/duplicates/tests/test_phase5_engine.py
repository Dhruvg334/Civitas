"""Phase 5 tests: duplicate detection engine — related categories, ✓ reasons,
cluster IDs, incident density and the labelled evaluation harness."""

from datetime import datetime, timedelta, timezone

import pytest

from civitas_duplicates import DuplicateDetector  # noqa: F401  (engine smoke)
from civitas_duplicates.contracts import PairFeatures, ReportLike
from civitas_duplicates.detector import DENSITY_CELL_SIZE_M
from civitas_duplicates.evaluation import (
    EngineEvaluation,
    build_labelled_pairs,
    evaluate_engine,
    gps_margin_check,
)
from civitas_duplicates.similarity import decide_duplicate, duplicate_reasons
from civitas_duplicates.signals import (
    RELATED_CATEGORIES,
    category_agreement,
    category_relation,
)

T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)


def report(
    report_id: str,
    description: str,
    lat: float = 28.6139,
    lon: float = 77.2090,
    category: str = "water leak",
    submitted_at: datetime = T0,
    **kw,
) -> ReportLike:
    return ReportLike(
        report_id=report_id,
        description=description,
        latitude=lat,
        longitude=lon,
        submitted_at=submitted_at,
        category=category,
        **kw,
    )


class TestRelatedCategories:
    def test_related_categories_score_half(self):
        score, note = category_relation("water leak", "road damage")
        assert score == pytest.approx(0.5)
        assert note and "road surface" in note

    def test_identical_categories_score_one(self):
        assert category_relation("flooding", "water leak") == (1.0, None)
        assert category_agreement("waste", "garbage overflow") == 1.0

    def test_conflicting_categories_zero(self):
        score, note = category_relation("streetlight", "garbage")
        assert score == 0.0
        assert note is None

    def test_related_pairs_are_documented(self):
        pair_keys = {tuple(sorted(p)) for p in RELATED_CATEGORIES}
        assert ("pothole", "water_leak") in pair_keys
        assert ("garbage", "water_leak") in pair_keys

    def test_related_categories_merge_with_note(self):
        pair = PairFeatures(
            text_similarity=0.5, image_similarity=None, category_agreement=0.5,
            gps_similarity=0.95, gps_distance_m=60.0, time_similarity=0.9,
            time_delta_h=4.0, landmark_similarity=1.0,
            category_relation_note="water damage erodes the road surface",
        )
        is_dup, basis, review = decide_duplicate(pair)
        assert is_dup
        assert not review
        assert any("related categories" in b for b in basis)

    def test_true_conflict_still_reviewed(self):
        pair = PairFeatures(
            text_similarity=0.5, image_similarity=None, category_agreement=0.0,
            gps_similarity=0.98, gps_distance_m=20.0, time_similarity=0.95,
            time_delta_h=3.0, landmark_similarity=1.0,
        )
        is_dup, _, review = decide_duplicate(pair)
        assert not is_dup
        assert review


class TestReasonsChecklist:
    def test_reasons_include_evidence_based_checks(self):
        pair = PairFeatures(
            text_similarity=0.8, image_similarity=0.9, category_agreement=1.0,
            gps_similarity=0.99, gps_distance_m=34.0, time_similarity=0.95,
            time_delta_h=2.5, landmark_similarity=1.0, incident_density=0.4,
        )
        reasons = duplicate_reasons(pair)
        assert any("34 m apart" in r for r in reasons)
        assert any("2.5 h apart" in r for r in reasons)
        assert any("landmark" in r for r in reasons)
        assert any("image similarity 0.90" in r for r in reasons)
        assert any("text similarity 0.80" in r for r in reasons)
        assert any("incident density 0.40" in r for r in reasons)

    def test_missing_image_not_listed(self):
        pair = PairFeatures(
            text_similarity=0.3, image_similarity=None, category_agreement=0.0,
            gps_similarity=0.1, gps_distance_m=9000.0, time_similarity=0.05,
            time_delta_h=300.0, landmark_similarity=0.0,
        )
        reasons = duplicate_reasons(pair)
        assert not any("image" in r for r in reasons)


class TestEnginePhase5:
    def test_engine_defaults_to_incident_anchored_weights(self):
        engine = DuplicateDetector()
        assert "incident_density" in engine.config.weights
        assert sum(engine.config.weights.values()) == pytest.approx(1.0)

    def test_cluster_ids_are_cl_sequence(self):
        engine = DuplicateDetector(cluster_id_start=18)
        a = report("r1", "deep pothole near school gate causing accidents")
        b = report("r2", "big pothole before school gate, two wheelers slipping",
                   lat=28.6140, lon=77.2092, submitted_at=T0 + timedelta(hours=2))
        c = report("r3", "streetlight flickering near metro", category="streetlight",
                   lat=28.6190, lon=77.2165, submitted_at=T0 + timedelta(days=2))
        clusters = engine.cluster([a, b, c])
        merged = next(cl for cl in clusters if cl.member_count > 1)
        assert merged.cluster_id == "CL-018"
        assert merged.report_ids == ["r1", "r2"]

    def test_cluster_id_start_must_be_positive(self):
        from civitas_duplicates.cluster import cluster_reports

        with pytest.raises(ValueError):
            cluster_reports([], [], cluster_id_start=0)

    def test_incident_density_feature_from_records(self):
        engine = DuplicateDetector(
            density_records=[
                {"incident_id": f"i-{i}", "latitude": 28.6131 + i * 0.00001,
                 "longitude": 77.2090, "category": "pothole"}
                for i in range(60)
            ]
        )
        a = report("r1", "pothole near the school gate", lat=28.6131, lon=77.2090)
        b = report("r2", "pothole in front of the school", lat=28.6132,
                   lon=77.20901, submitted_at=T0 + timedelta(hours=1))
        res = engine.evaluate_pair(a, b)
        assert res.feature_contributions["incident_density"] > 0.9
        assert any("incident density" in line for line in res.decision_basis)

    def test_evaluate_pair_returns_reasons(self):
        engine = DuplicateDetector()
        a = report("r1", "water leak on kingsway junction road", category="water leak",
                   lat=28.6160, lon=77.2130)
        b = report("r2", "water leak kingsway junction, road flooding", category="water leak",
                   lat=28.6162, lon=77.2132, submitted_at=T0 + timedelta(hours=1))
        res = engine.evaluate_pair(a, b)
        assert res.is_duplicate
        assert res.reasons
        assert any(r.startswith("✓") for r in res.reasons)

    def test_related_categories_merge_all_three(self):
        """R1 water leak, R2 flooding, R3 road damage -> one CL cluster."""
        engine = DuplicateDetector()
        r1 = report("R1", "water leaking from the main pipe near sunrise school", category="water leak")
        r2 = report("R2", "flooding on the road in front of sunrise school", category="flooding",
                    lat=28.6140, lon=77.2091, submitted_at=T0 + timedelta(minutes=30))
        r3 = report("R3", "road surface breaking up after the water near the school", category="road damage",
                    lat=28.6141, lon=77.2092, submitted_at=T0 + timedelta(minutes=75))
        clusters = engine.cluster([r1, r2, r3])
        merged = next(cl for cl in clusters if cl.member_count > 1)
        assert set(merged.report_ids) == {"R1", "R2", "R3"}
        assert merged.member_count == 3
        assert merged.span_m < 200.0


class TestEvaluationHarness:
    def test_labelled_pairs_respect_geometry(self):
        pairs = build_labelled_pairs(seed=11, n_per_label=3, with_images=False)
        gps_margin_check(pairs)
        assert len(pairs) == 9
        labels = [p.label for p in pairs]
        assert labels.count("positive") == 3
        assert labels.count("negative") == 3
        assert labels.count("ambiguous") == 3

    def test_evaluate_engine_metrics_and_failure_modes(self):
        pairs = build_labelled_pairs(seed=11, n_per_label=3, with_images=False)
        ev = evaluate_engine(pairs)
        assert isinstance(ev, EngineEvaluation)
        assert ev.n_positive == 3 and ev.n_negative == 3 and ev.n_ambiguous == 3
        assert 0.0 <= ev.precision <= 1.0
        assert 0.0 <= ev.recall <= 1.0
        assert 0.0 <= ev.f1 <= 1.0
        assert 0.0 <= ev.accuracy <= 1.0
        assert ev.false_merges_total == ev.false_positives + ev.ambiguous_merged
        assert ev.false_splits_total == ev.false_negatives
        assert ev.true_positives + ev.false_negatives == ev.n_positive
        assert ev.false_positives + ev.true_negatives == ev.n_negative
        assert "false merges" in ev.summary()

    def test_all_positives_merged(self):
        pairs = build_labelled_pairs(seed=11, n_per_label=3, with_images=False)
        ev = evaluate_engine(pairs)
        assert ev.true_positives == ev.n_positive
        assert ev.false_splits_total == 0

    def test_negatives_not_merged(self):
        pairs = build_labelled_pairs(seed=11, n_per_label=3, with_images=False)
        ev = evaluate_engine(pairs)
        assert ev.true_negatives == ev.n_negative
        assert ev.false_merges_total == 0

    def test_ambiguity_escalated(self):
        pairs = build_labelled_pairs(seed=11, n_per_label=3, with_images=False)
        ev = evaluate_engine(pairs)
        assert ev.ambiguous_merged == 0
        assert ev.ambiguous_reviewed == ev.n_ambiguous

    def test_density_cell_size_constant(self):
        assert DENSITY_CELL_SIZE_M == 200.0