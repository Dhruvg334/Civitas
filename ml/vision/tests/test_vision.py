"""Tests for the Phase 3 computer vision pipeline.

Covers media quality gating, frame selection, real feature measurements,
the k-NN classifier with confidence, evidence extraction rules, the
end-to-end detector (image + video frames) and the benchmark evaluation
report. Synthetic benchmark images provide the ground truth; real-photo
coverage is a recorded limitation, not a claim.
"""

from datetime import datetime, timezone

import numpy as np
import pytest
from civitas_vision import evidence as evidence_rules
from civitas_vision.benchmark import (
    gaussian_blur,
    make_image,
    run_evaluation,
    train_default_model,
)
from civitas_vision.classifier import (
    KNNClassifier,
    merge_media_probs,
    secondary_categories,
)
from civitas_vision.contracts import CIVITAS_CATEGORIES, ClassificationProbs
from civitas_vision.detector import VisualIntelligencePipeline
from civitas_vision.features import FEATURE_NAMES, extract_features
from civitas_vision.frames import select_key_frames
from civitas_vision.quality import assess_quality, laplacian_variance
from PIL import Image

TODAY = datetime.now(timezone.utc).isoformat()


class TestQuality:
    def test_sharp_synthetic_image_is_usable(self):
        q = assess_quality(make_image("pothole_road_damage", 8000))
        assert q.usable
        assert q.blur_score > 0.001
        assert q.basis  # measurements are always traced

    def test_gaussian_blur_rejected_as_unusable(self):
        sharp = make_image("pothole_road_damage", 8000)
        blurred = gaussian_blur(sharp, radius=4.0)
        q_sharp = assess_quality(sharp)
        q_blur = assess_quality(blurred)
        assert q_sharp.usable and not q_blur.usable
        assert q_blur.blur_score < q_sharp.blur_score
        assert any("blurry" in r for r in q_blur.reasons)

    def test_tiny_image_rejected(self):
        img = Image.new("RGB", (16, 16), (80, 80, 80))
        q = assess_quality(img)
        assert not q.usable
        assert any("resolution" in r for r in q.reasons)

    def test_near_black_rejected(self):
        img = Image.new("RGB", (160, 160), (2, 2, 2))
        q = assess_quality(img)
        assert not q.usable
        assert any("near-black" in r for r in q.reasons)

    def test_laplacian_variance_zero_on_flat(self):
        flat = np.full((32, 32), 0.5)
        assert laplacian_variance(flat) == 0.0


class TestFrames:
    def test_key_frame_selection_prefers_sharp(self):
        sharp = make_image("broken_streetlight", 8100)
        blurred = gaussian_blur(sharp, radius=5.0)
        picks = select_key_frames([blurred, sharp], top_k=1)
        assert len(picks) == 1 and picks[0].index == 1

    def test_deterministic_on_ties_and_rejects_unusable(self):
        black = Image.new("RGB", (128, 128), (1, 1, 1))
        sharp = make_image("pothole_road_damage", 8101)
        picks = select_key_frames([black, sharp, black], top_k=2)
        assert [p.index for p in picks] == [1, 2]
        assert picks[0].quality.usable and not picks[1].quality.usable

    def test_fully_unusable_video_still_rejected(self):
        black = Image.new("RGB", (128, 128), (1, 1, 1))
        assert select_key_frames([black, black, black], top_k=2) == []

    def test_key_frames_cover_all_time_segments(self):
        sharp = [make_image("water_leakage", 8102 + i) for i in range(8)]
        picks = select_key_frames(sharp, top_k=4)
        segments = sorted({p.index // 2 for p in picks})
        assert segments == [0, 1, 2, 3]

    def test_segments_without_usable_frames_contribute_best_available(self):
        black = Image.new("RGB", (128, 128), (1, 1, 1))
        sharp = make_image("broken_streetlight", 8103)
        picks = select_key_frames([sharp, black, black, black], top_k=4)
        assert [p.index for p in picks] == [0, 1, 2, 3]


class TestFeatures:
    def test_measurement_set_complete_and_bounded(self):
        f = extract_features(make_image("garbage_overflow", 8200))
        assert set(FEATURE_NAMES) == set(f.keys())
        assert len(f) == len(FEATURE_NAMES)
        for v in f.values():
            assert isinstance(v, float) and v >= 0.0

    def test_deterministic(self):
        a = extract_features(make_image("water_leakage", 8201))
        b = extract_features(make_image("water_leakage", 8201))
        assert a == b

    def test_water_measurements_dominate_blue_features(self):
        water = extract_features(make_image("water_leakage", 8202))
        tree = extract_features(make_image("fallen_tree", 8203))
        assert water["blue_smooth_share"] > tree["blue_smooth_share"] + 0.2
        assert water["dark_lowtexture_share"] < 0.1


class TestClassifier:
    def setup_method(self):
        self.model = train_default_model()

    def test_known_image_classified_correctly(self):
        for cat in CIVITAS_CATEGORIES:
            img = make_image(cat, 9000)
            probs = self.model.predict_proba(extract_features(img))
            assert probs.primary_category == cat
            assert 0.0 <= probs.confidence <= 1.0
            assert set(probs.probabilities) == set(CIVITAS_CATEGORIES)

    def test_knn_fit_required(self):
        fresh = KNNClassifier()
        with pytest.raises(RuntimeError):
            fresh.predict_proba({"edge_density": 0.1})

    def test_merge_averages_probabilities(self):
        a = ClassificationProbs(probabilities={c: 0.8 if c == "pothole_road_damage" else 0.0 for c in CIVITAS_CATEGORIES}, primary_category="pothole_road_damage", confidence=0.8)
        b = ClassificationProbs(probabilities={c: 0.7 if c == "pothole_road_damage" else 0.0 for c in CIVITAS_CATEGORIES}, primary_category="pothole_road_damage", confidence=0.7)
        merged = merge_media_probs([a, b])
        assert merged.primary_category == "pothole_road_damage"
        assert merged.probabilities["pothole_road_damage"] == pytest.approx(0.75)

    def test_secondary_categories_threshold(self):
        probs = {"pothole_road_damage": 0.6, "water_leakage": 0.3, "garbage_overflow": 0.1}
        out = secondary_categories(probs, "pothole_road_damage")
        assert out == ["water_leakage"]


class TestEvidence:
    def test_standing_water_evidence(self):
        img = make_image("water_leakage", 9100, "default")
        ev, feats, basis = evidence_rules.evidence_for_image(img)
        assert "standing water" in ev
        assert feats["blue_smooth_share"] >= 0.20
        assert any("standing water" in b for b in basis)

    def test_flowing_water_evidence_on_flow_variant(self):
        ev, _, _ = evidence_rules.evidence_for_image(make_image("water_leakage", 9101, "flow"))
        assert "water flowing across road" in ev

    def test_no_garbage_evidence_on_fallen_tree(self):
        ev, _, _ = evidence_rules.evidence_for_image(make_image("fallen_tree", 9102))
        assert "mixed-color waste pile (scattered debris)" not in ev
        assert "fallen trunk/blockage spanning the road" in ev

    def test_streetlight_bulb_evidence(self):
        ev, _, _ = evidence_rules.evidence_for_image(make_image("broken_streetlight", 9103))
        assert "dark scene with a localized bright bulb region" in ev

    def test_evidence_filtered_by_category_support(self):
        ev = ["standing water", "water flowing across road"]
        assert evidence_rules.filter_evidence_for_categories(ev, {"water_leakage"}) == ev
        assert evidence_rules.filter_evidence_for_categories(ev, {"pothole_road_damage"}) == []


class TestPipeline:
    def setup_method(self):
        self.pipeline = VisualIntelligencePipeline()

    def test_structured_output_contract(self):
        res = self.pipeline.analyze_image(make_image("water_leakage", 9200, "flow"))
        payload = res.as_json()
        assert set(payload) == {
            "primary_category",
            "secondary_categories",
            "secondary_label",
            "precise_observable_description",
            "observable_evidence",
            "confidence",
        }
        assert payload["primary_category"] == "water_leakage"
        assert isinstance(payload["secondary_categories"], list)
        assert isinstance(payload["observable_evidence"], list) and payload["observable_evidence"]
        assert 0.0 <= payload["confidence"] <= 1.0
        assert res.media_usable and res.frames_selected == 1

    def test_all_five_categories_primary(self):
        for cat in CIVITAS_CATEGORIES:
            res = self.pipeline.analyze_image(make_image(cat, 9201))
            assert res.primary_category == cat, cat
            assert res.media_usable

    def test_blurred_media_rejected_with_basis(self):
        res = self.pipeline.analyze_image(gaussian_blur(make_image("pothole_road_damage", 9202), 4.0))
        assert not res.media_usable
        assert res.primary_category is None
        assert res.basis

    def test_video_frames_selection_and_classification(self):
        sharp = make_image("garbage_overflow", 9203)
        frames = [gaussian_blur(sharp, 5.0), sharp, gaussian_blur(sharp, 6.0)]
        res = self.pipeline.analyze_video("unused.mp4", video_extra_frames=frames)
        assert res.media_usable and res.frames_selected >= 1
        assert res.primary_category == "garbage_overflow"

    def test_video_no_usable_frames(self):
        black = Image.new("RGB", (128, 128), (1, 1, 1))
        res = self.pipeline.analyze_video("unused.mp4", video_extra_frames=[black, black])
        assert not res.media_usable
        assert "no usable frames" in " ".join(res.basis)


class TestBenchmark:
    def test_report_structure_and_performance(self):
        rep = run_evaluation()
        assert rep.n_samples == 40
        assert rep.accuracy >= 0.85
        assert rep.macro_f1 >= 0.85
        assert set(rep.per_class) == set(CIVITAS_CATEGORIES)
        assert len(rep.confusion_matrix) == 5 and all(len(r) == 5 for r in rep.confusion_matrix)
        total = sum(map(sum, rep.confusion_matrix))
        assert total == rep.n_samples

    def test_report_deterministic(self):
        a = run_evaluation()
        b = run_evaluation()
        assert a.accuracy == b.accuracy and a.confusion_matrix == b.confusion_matrix


class TestNoRealPhotoClaims:
    def test_basis_marks_synthetic_training(self):
        rep = run_evaluation()
        assert any("synthetic" in b for b in rep.basis)