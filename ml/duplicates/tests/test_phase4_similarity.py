"""Phase 4 tests: image embeddings, incident-anchored similarity, pair benchmark."""

from datetime import datetime, timedelta, timezone

import pytest

from civitas_duplicates.benchmark import make_synthetic_pairs, run_pair_evaluation
from civitas_duplicates.contracts import PairFeatures
from civitas_duplicates.embeddings import (
    ClassicalImageEmbedder,
    HashNgramEmbedder,
    ImageEmbedding,
    build_report_embeddings,
)
from civitas_duplicates.geo_features import gps_distance_m
from civitas_duplicates.similarity import (
    INCIDENT_ANCHORED_WEIGHTS,
    ScoringConfig,
    incident_gate,
    incident_similarity,
    make_pair,
)

T0 = datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc)
CENTER = (28.6139, 77.2090)


def _solid_image(rgb=(40, 70, 120)):
    from PIL import Image

    return Image.new("RGB", (48, 48), rgb)


def _build(
    report_id: str,
    description: str,
    embedder: HashNgramEmbedder,
    gps=CENTER,
    submitted_at: datetime = T0,
    category: str = "water_leak",
    landmark_ids=None,
    image=None,
    image_embedder=None,
):
    return build_report_embeddings(
        report_id=report_id,
        description=description,
        text_embedder=embedder,
        image=image,
        image_embedder=image_embedder,
        gps=gps,
        submitted_at=submitted_at.isoformat(),
        category=category,
        landmark_ids=landmark_ids or [],
    )


class TestClassicalImageEmbedder:
    def test_vector_shape_and_normalization(self):
        embedder = ClassicalImageEmbedder()
        emb = embedder.embed_image(_solid_image())
        assert isinstance(emb, ImageEmbedding)
        try:
            from civitas_vision.features import FEATURE_NAMES  # noqa: F401

            expected = len(FEATURE_NAMES) + embedder.HUE_BINS + embedder.SAT_BINS
        except ImportError:
            from civitas_duplicates.embeddings import _VISION_FEATURE_ORDER

            expected = len(_VISION_FEATURE_ORDER) + embedder.HUE_BINS + embedder.SAT_BINS
        assert emb.dim == expected
        assert emb.method.startswith("classical-features")
        assert emb.basis
        norm = sum(v * v for v in emb.vector) ** 0.5
        assert norm == pytest.approx(1.0, abs=1e-3)

    def test_deterministic(self):
        embedder = ClassicalImageEmbedder()
        a = embedder.embed_image(_solid_image()).vector
        b = embedder.embed_image(_solid_image()).vector
        assert a == b

    def test_protocol_compat_bytes(self):
        embedder = ClassicalImageEmbedder()
        from io import BytesIO

        buf = BytesIO()
        _solid_image().save(buf, format="PNG")
        vec = embedder.embed(buf.getvalue())
        assert len(vec) > 0

    def test_different_colours_different_vectors(self):
        embedder = ClassicalImageEmbedder()
        a = embedder.embed_image(_solid_image((40, 70, 120))).vector
        b = embedder.embed_image(_solid_image((200, 120, 40))).vector
        assert a != b


class TestReportEmbeddings:
    def test_text_always_image_optional(self):
        e = HashNgramEmbedder()
        with_image = _build("r1", "water leak near school", e, image=_solid_image(),
                            image_embedder=ClassicalImageEmbedder())
        without_image = _build("r2", "water leak near school", e)
        assert len(with_image.text_embedding) == 512
        assert with_image.image_embedding is not None
        assert without_image.image_embedding is None
        assert any("no image supplied" in b for b in without_image.basis)

    def test_gps_category_landmarks_carried(self):
        e = HashNgramEmbedder()
        rep = _build("r3", "pothole", e, gps=(1.0, 2.0), category="pothole",
                     landmark_ids=["lm-1"])
        assert rep.gps == (1.0, 2.0)
        assert rep.category == "pothole"
        assert rep.landmark_ids == ["lm-1"]


def _dup_report(embedder: HashNgramEmbedder, rid: str, offset_km: float = 0.0,
                hours: float = 1.0):
    return _build(
        rid,
        "pipe burst spraying water across the footpath",
        embedder,
        gps=(CENTER[0] - offset_km * 0.009, CENTER[1] + offset_km * 0.009),
        submitted_at=T0 + timedelta(hours=hours),
        category="water_leak",
        landmark_ids=["lm-school-1"],
        image=_solid_image(),
        image_embedder=ClassicalImageEmbedder(),
    )


class TestIncidentGate:
    def test_gate_passes_near_pair(self):
        pair = PairFeatures(
            text_similarity=0.5, category_agreement=1.0, gps_similarity=0.9,
            gps_distance_m=400.0, time_similarity=0.8, time_delta_h=12.0,
            landmark_similarity=0.6,
        )
        gate = incident_gate(pair)
        assert gate.incident_possible
        assert any("plausible" in r for r in gate.reasons)

    def test_gate_rejects_far_distance(self):
        pair = PairFeatures(
            text_similarity=0.9, category_agreement=1.0, gps_similarity=0.1,
            gps_distance_m=5_000.0, time_similarity=0.8, time_delta_h=5.0,
            landmark_similarity=0.0,
        )
        gate = incident_gate(pair)
        assert not gate.incident_possible
        assert any("apart" in r for r in gate.reasons)

    def test_gate_rejects_time_window(self):
        pair = PairFeatures(
            text_similarity=0.9, category_agreement=1.0, gps_similarity=0.9,
            gps_distance_m=100.0, time_similarity=0.01, time_delta_h=200.0,
            landmark_similarity=0.5,
        )
        gate = incident_gate(pair)
        assert not gate.incident_possible
        assert any("h apart" in r for r in gate.reasons)


class TestIncidentSimilarity:
    def test_same_incident_is_duplicate(self):
        e = HashNgramEmbedder()
        a = _dup_report(e, "a")
        b = _dup_report(e, "b", hours=2.0)
        result = incident_similarity(a, b, weights=INCIDENT_ANCHORED_WEIGHTS)
        assert result.incident_possible
        assert result.is_duplicate
        assert result.score >= 0.7
        assert result.contributions["gps_similarity"] > 0.5

    def test_far_pair_answered_with_geospatial_evidence(self):
        e = HashNgramEmbedder()
        a = _dup_report(e, "a")
        b = _dup_report(e, "b", offset_km=6.0, hours=2.0)
        result = incident_similarity(a, b)
        assert not result.incident_possible
        assert not result.is_duplicate
        assert result.score == 0.0
        assert any("geospatial evidence" in line for line in result.decision_basis)

    def test_missing_gps_escalates_to_review(self):
        e = HashNgramEmbedder()
        a = _build("a", "water leak", e, gps=None, image=_solid_image(),
                   image_embedder=ClassicalImageEmbedder())
        b = _dup_report(e, "b")
        result = incident_similarity(a, b)
        assert not result.incident_possible
        assert result.requires_review
        assert not result.is_duplicate
        assert any("GPS signal missing" in line for line in result.decision_basis)

    def test_make_pair_uses_real_embeddings(self):
        e = HashNgramEmbedder()
        a = _dup_report(e, "a")
        b = _dup_report(e, "b")
        pair = make_pair(a, b)
        from civitas_duplicates.embeddings import cosine_similarity

        assert pair.text_similarity == pytest.approx(
            cosine_similarity(a.text_embedding, b.text_embedding)
        )
        assert pair.category_agreement == 1.0
        assert pair.gps_distance_m == pytest.approx(
            gps_distance_m(a.gps[0], a.gps[1], b.gps[0], b.gps[1])
        )

    def test_missing_text_embedding_raises(self):
        e = HashNgramEmbedder()
        a = _dup_report(e, "a")
        b = _dup_report(e, "b").model_copy(update={"text_embedding": []})
        with pytest.raises(ValueError):
            incident_similarity(a, b)


class TestBenchmark:
    def test_synthetic_pair_labels(self):
        pairs = make_synthetic_pairs(seed=7, n_duplicates=3, n_distinct=3)
        assert len(pairs) == 6
        assert [label for _, _, label in pairs] == [1, 1, 1, 0, 0, 0]
        dup = pairs[0]
        assert dup[0].category == dup[1].category
        assert gps_distance_m(
            dup[0].gps[0], dup[0].gps[1], dup[1].gps[0], dup[1].gps[1]
        ) < 2_000.0
        distinct_a, distinct_b, _ = pairs[3]
        assert (
            gps_distance_m(
                distinct_a.gps[0], distinct_a.gps[1],
                distinct_b.gps[0], distinct_b.gps[1],
            )
            > 2_000.0
        )

    def test_pair_evaluation_runs_and_reports_metrics(self):
        ev = run_pair_evaluation(seed=7, n_duplicates=2, n_distinct=2)
        assert ev.n_duplicates == 2
        assert ev.n_distinct == 2
        assert 0.0 <= ev.accuracy <= 1.0
        assert 0.0 <= ev.precision <= 1.0
        assert 0.0 <= ev.recall <= 1.0
        assert 0.0 <= ev.f1 <= 1.0
        assert ev.review_flag_count >= 0
        assert "incident_anchored" in ev.summary()

    def test_anchored_weights_sum_to_one(self):
        assert sum(INCIDENT_ANCHORED_WEIGHTS.values()) == pytest.approx(1.0)


class TestScoringConfigValidation:
    def test_bad_weights_rejected(self):
        with pytest.raises(ValueError):
            ScoringConfig(weights={"text_similarity": 0.2})