"""Tests for civitas_duplicates: embeddings, signals, scoring, clustering."""

from datetime import datetime, timedelta, timezone

import pytest
from civitas_duplicates.contracts import PairFeatures, ReportLike
from civitas_duplicates.detector import DuplicateDetector
from civitas_duplicates.embeddings import HashNgramEmbedder, cosine_similarity
from civitas_duplicates.geo_features import gps_similarity, within_duplicate_radius_m
from civitas_duplicates.similarity import (
    ScoringConfig,
    composite_score,
    decide_duplicate,
)
from civitas_duplicates.time_features import time_similarity, within_burst_window_hours

T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)


def report(
    report_id: str,
    description: str,
    lat: float = 28.6139,
    lon: float = 77.2090,
    submitted_at: datetime = T0,
    category: str | None = "pothole",
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


class TestEmbeddings:
    def test_hash_embedder_deterministic(self):
        e = HashNgramEmbedder()
        a = e.embed("deep pothole near school gate on main road")
        b = e.embed("deep pothole near school gate on main road")
        assert a == b
        assert cosine_similarity(a, b) == pytest.approx(1.0)

    def test_similar_text_similar(self):
        e = HashNgramEmbedder()
        a = e.embed("large pothole in front of the school causing two wheelers to slip")
        b = e.embed("big pothole before school gate, two wheelers slipping, needs repair")
        # Same words in shuffled order -> high cosine (hash bag-of-ngrams)
        assert 0.5 < cosine_similarity(a, b) <= 1.0

    def test_dissimilar_text_low_similarity(self):
        e = HashNgramEmbedder()
        a = e.embed("streetlight not working near the metro station")
        b = e.embed("garbage overflowing at the old bazaar market")
        assert cosine_similarity(a, b) < 0.4

    def test_empty_text(self):
        e = HashNgramEmbedder()
        vec = e.embed("")
        assert len(vec) == 512
        assert cosine_similarity(vec, e.embed("anything")) >= 0.0


class TestGeoFeatures:
    def test_gps_similarity_identity(self):
        sim, d = gps_similarity(28.6139, 77.2090, 28.6139, 77.2090)
        assert sim == pytest.approx(1.0)
        assert d == 0.0

    def test_gps_similarity_decay(self):
        sim_near, _ = gps_similarity(28.6139, 77.2090, 28.6142, 77.2093)  # ~40m
        sim_far, _ = gps_similarity(28.6139, 77.2090, 28.6239, 77.2190)  # ~1.4km
        assert sim_near > 0.9 > sim_far

    def test_radius_gate(self):
        assert within_duplicate_radius_m(1500.0)
        assert not within_duplicate_radius_m(2500.0)


class TestTimeFeatures:
    def test_time_similarity_same_minute(self):
        sim, dh = time_similarity(T0, T0 + timedelta(minutes=10))
        assert dh == pytest.approx(0.1667, abs=0.01)
        assert sim > 0.99

    def test_time_similarity_far_apart(self):
        sim, _ = time_similarity(T0, T0 + timedelta(days=30))
        assert sim < 0.01

    def test_burst_window(self):
        assert within_burst_window_hours(48.0)
        assert not within_burst_window_hours(120.0)

    def test_naive_datetime_accepted(self):
        sim, _ = time_similarity(datetime(2026, 3, 1, 10, 0), T0)
        assert sim == pytest.approx(1.0)


class TestScoring:
    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError):
            ScoringConfig(weights={"text_similarity": 0.5})

    def test_composite_respects_threshold(self):
        strong = PairFeatures(
            text_similarity=0.9, image_similarity=0.95, category_agreement=1.0,
            gps_similarity=0.95, gps_distance_m=20.0, time_similarity=0.99,
            time_delta_h=0.5, landmark_similarity=1.0,
        )
        assert composite_score(strong) >= 0.7
        is_dup, _, review = decide_duplicate(strong)
        assert is_dup
        assert not review

    def test_weak_pair_rejected(self):
        weak = PairFeatures(
            text_similarity=0.2, image_similarity=None, category_agreement=0.0,
            gps_similarity=0.01, gps_distance_m=5000.0, time_similarity=0.01,
            time_delta_h=500.0, landmark_similarity=0.0,
        )
        assert composite_score(weak) < 0.7
        is_dup, _, _ = decide_duplicate(weak)
        assert not is_dup

    def test_missing_image_renormalizes(self):
        with_image = PairFeatures(
            text_similarity=0.6, image_similarity=0.6, category_agreement=1.0,
            gps_similarity=0.5, gps_distance_m=100.0, time_similarity=0.9,
            time_delta_h=2.0, landmark_similarity=0.4,
        )
        without_image = with_image.model_copy(update={"image_similarity": None})
        assert composite_score(without_image) > composite_score(with_image)

    def test_exceptional_override(self):
        pair = PairFeatures(
            text_similarity=0.85, image_similarity=None, category_agreement=1.0,
            gps_similarity=0.5, gps_distance_m=400.0, time_similarity=0.8,
            time_delta_h=10.0, landmark_similarity=0.2,
        )
        is_dup, basis, review = decide_duplicate(pair)
        assert is_dup
        assert not review
        assert any("override" in b for b in basis)

    def test_cross_category_same_spot_requires_review(self):
        pair = PairFeatures(
            text_similarity=0.5, image_similarity=None, category_agreement=0.0,
            gps_similarity=0.98, gps_distance_m=20.0, time_similarity=0.95,
            time_delta_h=3.0, landmark_similarity=1.0,
        )
        is_dup, basis, review = decide_duplicate(pair)
        assert not is_dup
        assert review
        assert any("review" in b.lower() for b in basis)

    def test_near_threshold_flags_review(self):
        pair = PairFeatures(
            text_similarity=0.5, image_similarity=None, category_agreement=1.0,
            gps_similarity=0.6, gps_distance_m=300.0, time_similarity=0.6,
            time_delta_h=20.0, landmark_similarity=0.4,
        )
        is_dup, basis, review = decide_duplicate(pair)
        assert not is_dup
        assert review


class TestDetector:
    def test_cluster_merges_true_duplicates(self):
        d = DuplicateDetector()
        a = report("r1", "deep pothole near school gate causing accidents", lat=28.6139, lon=77.2090)
        b = report("r2", "big pothole before school gate, two wheelers slipping", lat=28.6140, lon=77.2092, submitted_at=T0 + timedelta(hours=2))
        c = report("r3", "streetlight flickering near metro", lat=28.6190, lon=77.2165, submitted_at=T0 + timedelta(days=2), category="streetlight")
        clusters = d.cluster([a, b, c])
        merged = [cl for cl in clusters if cl.member_count > 1]
        assert len(merged) == 1
        assert set(merged[0].report_ids) == {"r1", "r2"}
        assert merged[0].representative_report_id in {"r1", "r2"}
        isolated = [cl for cl in clusters if cl.member_count == 1]
        assert [cl.report_ids[0] for cl in isolated] == ["r3"]

    def test_evaluate_pair_reports_match(self):
        d = DuplicateDetector()
        a = report("r1", "water leak on kingsway junction road", category="water leak", lat=28.6160, lon=77.2130)
        b = report("r2", "water leak kingsway junction, road flooding", category="water leak", lat=28.6162, lon=77.2132, submitted_at=T0 + timedelta(hours=1))
        res = d.evaluate_pair(a, b)
        assert res.is_duplicate
        assert res.matched_incident_id == "r2"
        assert res.feature_contributions["landmark_similarity"] > 0.5
        assert any("landmark" in b for b in res.decision_basis)

    def test_find_duplicate_of(self):
        d = DuplicateDetector()
        existing = report("r1", "broken streetlight civic centre metro", category="streetlight", lat=28.6190, lon=77.2165)
        new = report("r9", "streetlight not working outside civic centre metro", category="streetlight", lat=28.6191, lon=77.2166, submitted_at=T0 + timedelta(hours=5))
        distant = report("r10", "garbage overflowing old bazaar", category="garbage", lat=28.6120, lon=77.2180, submitted_at=T0 + timedelta(days=3))
        match = d.find_duplicate_of(new, [existing, distant])
        assert match is not None
        assert match.matched_incident_id == "r1"
        assert match.is_duplicate

    def test_no_duplicate_when_distinct(self):
        d = DuplicateDetector()
        a = report("r1", "pothole near park", lat=28.6180, lon=77.2070)
        b = report("r2", "garbage overflowing at market", category="garbage", lat=28.6120, lon=77.2180, submitted_at=T0 + timedelta(days=10))
        res = d.evaluate_pair(a, b)
        assert not res.is_duplicate
        assert res.matched_incident_id is None

    def test_spatial_prefilter_path(self):
        d = DuplicateDetector()
        a = report("r1", "pothole kingsway junction", lat=28.6160, lon=77.2130)
        b = report("r2", "pothole kingsway junction deep", lat=28.6161, lon=77.2130)
        clusters = d.cluster([a, b], spatial_prefilter=[("r1", "r2")])
        assert any(cl.member_count == 2 for cl in clusters)

    def test_singleton_report_cluster(self):
        d = DuplicateDetector()
        clusters = d.cluster([report("solo", "single report")])
        assert len(clusters) == 1
        assert clusters[0].member_count == 1