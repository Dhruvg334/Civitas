"""Tests for the zero-shot CLIP real-media classifier (real-media track).

Covers the deterministic calibration math (category prompt pooling, CLIP
softmax scale, margin confidence, zero-shot OOD ratio, subcategory
selection) with fabricated similarity maps — no model, no network. The
real-model integration test runs only when transformers + torch are
installed and the checkpoint can be loaded (skipped otherwise, like the
video tests' cv2 guard).

The design contract under test: inference is deterministic, probabilities
cover the nine real-media categories (the five core Civitas categories plus
`other_infrastructure_damage`, `drainage_damage`, `no_incident`,
`pest_infestation`), confidence is the top-1/top-2 softmax margin, the
out-of-distribution ratio is
`OOD_REFERENCE_SIMILARITY / best_category_similarity` (the product's 2.0
uncertainty floor sits at best similarity 0.22), and the secondary label is
the best subcategory similarity above `SUBCATEGORY_EMISSION_FLOOR`.
"""

import pytest
from civitas_vision.clip_classifier import (
    CATEGORY_LABELS,
    CATEGORY_PROMPTS,
    OOD_REFERENCE_SIMILARITY,
    SUBCATEGORY_EMISSION_FLOOR,
    SUBCATEGORY_PROMPTS,
    calibrate,
    category_prompt_scores,
    ood_ratio_from_best_similarity,
    pick_secondary_label,
    subcategory_scores_from_similarity,
)
from civitas_vision.contracts import REAL_MEDIA_CATEGORIES


def _similarity_map(scores: dict[str, float]) -> dict[str, float]:
    """A similarity map covering every prompt (missing prompts default low)."""
    out = {}
    for prompts in CATEGORY_PROMPTS.values():
        for prompt in prompts:
            out[prompt] = scores.get(prompt, 0.10)
    return out


class TestCategoryPromptScores:
    def test_best_prompt_per_category(self):
        sims = _similarity_map(
            {
                CATEGORY_PROMPTS["water_leakage"][0]: 0.34,
                CATEGORY_PROMPTS["water_leakage"][1]: 0.42,
                CATEGORY_PROMPTS["pothole_road_damage"][0]: 0.31,
            }
        )
        scores = category_prompt_scores(sims, CATEGORY_PROMPTS)
        assert scores["water_leakage"] == pytest.approx(0.42)
        assert scores["pothole_road_damage"] == pytest.approx(0.31)
        assert set(scores) == set(REAL_MEDIA_CATEGORIES)

    def test_all_categories_have_prompts(self):
        for category in REAL_MEDIA_CATEGORIES:
            assert CATEGORY_PROMPTS[category], category

    def test_all_categories_have_labels(self):
        for category in REAL_MEDIA_CATEGORIES:
            assert CATEGORY_LABELS[category], category

    def test_prompts_are_distinct_across_categories(self):
        seen: set[str] = set()
        for prompts in CATEGORY_PROMPTS.values():
            for prompt in prompts:
                assert prompt not in seen
                seen.add(prompt)


class TestCalibrate:
    def test_decisive_category_gets_high_margin(self):
        scores = {c: 0.20 for c in REAL_MEDIA_CATEGORIES}
        scores["water_leakage"] = 0.42
        probs, margin, s_max = calibrate(scores)
        assert sum(probs) == pytest.approx(1.0, abs=1e-9)
        assert len(probs) == len(REAL_MEDIA_CATEGORIES)
        water = dict(zip(REAL_MEDIA_CATEGORIES, probs))["water_leakage"]
        assert water > 0.99
        assert margin > 0.95
        assert s_max == pytest.approx(0.42)

    def test_tied_best_pair_collapses_margin(self):
        scores = {c: 0.20 for c in REAL_MEDIA_CATEGORIES}
        scores["water_leakage"] = 0.31
        scores["pothole_road_damage"] = 0.31
        probs, margin, _ = calibrate(scores)
        assert margin < 0.01

    def test_uniform_scores_mean_zero_margin(self):
        scores = {c: 0.24 for c in REAL_MEDIA_CATEGORIES}
        _, margin, _ = calibrate(scores)
        assert margin == pytest.approx(0.0, abs=1e-9)


class TestOodRatio:
    def test_reference_similarity_is_ratio_one(self):
        assert ood_ratio_from_best_similarity(OOD_REFERENCE_SIMILARITY) == pytest.approx(1.0)

    def test_two_point_zero_floor_at_zero_point_two_two(self):
        assert ood_ratio_from_best_similarity(0.22) == pytest.approx(2.0, abs=0.01)
        assert ood_ratio_from_best_similarity(0.30) < 2.0
        assert ood_ratio_from_best_similarity(0.20) > 2.0

    def test_handles_zero_similarity(self):
        ratio = ood_ratio_from_best_similarity(0.0)
        assert ratio == OOD_REFERENCE_SIMILARITY / 1e-9


class TestSubcategories:
    def test_scores_are_scoped_to_the_primary_category(self):
        sims = {}
        for prompts in CATEGORY_PROMPTS.values():
            for prompt in prompts:
                sims[prompt] = 0.10
        for subcats in SUBCATEGORY_PROMPTS.values():
            for prompts in subcats.values():
                for prompt in prompts:
                    sims[prompt] = 0.12
        water_prompts = SUBCATEGORY_PROMPTS["water_leakage"]["Wall moisture damage"]
        sims[water_prompts[0]] = 0.44
        scoped = subcategory_scores_from_similarity(sims, SUBCATEGORY_PROMPTS, "water_leakage")
        assert set(scoped) == set(SUBCATEGORY_PROMPTS["water_leakage"])
        assert scoped["Wall moisture damage"] == pytest.approx(0.44)

    def test_unscoped_primary_has_no_subcategories(self):
        sims = {}
        for subcats in SUBCATEGORY_PROMPTS.values():
            for prompts in subcats.values():
                for prompt in prompts:
                    sims[prompt] = 0.20
        scoped = subcategory_scores_from_similarity(sims, SUBCATEGORY_PROMPTS, "fallen_tree")
        assert scoped == {}

    def test_secondary_label_requires_the_emission_floor(self):
        scores = {"Wall moisture damage": 0.20, "Roof leakage / building water damage": 0.19}
        label, _ = pick_secondary_label(scores)
        assert label is None

    def test_secondary_label_picks_best_above_floor(self):
        scores = {"Wall moisture damage": 0.31, "Roof leakage / building water damage": 0.29}
        label, adjusted = pick_secondary_label(scores)
        assert label == "Wall moisture damage"
        assert adjusted[label] == pytest.approx(0.31)

    def test_secondary_label_bonus_is_applied_and_recorded(self):
        scores = {"Open/unsafe drain": 0.28, "Blocked/damaged drainage": 0.30}
        label, adjusted = pick_secondary_label(
            scores, bonus_to="Open/unsafe drain", bonus=0.10
        )
        assert label == "Open/unsafe drain"
        assert adjusted["Open/unsafe drain"] == pytest.approx(0.38)

    def test_emission_floor_constant_sits_below_measured_subcategory_levels(self):
        assert SUBCATEGORY_EMISSION_FLOOR < 0.29


class TestRealModel:
    def test_real_media_probe_calibration_states(self):
        """The calibration points documented in the module docstring hold."""
        # In-manifold demo images measured >= 0.236 -> never flagged.
        assert ood_ratio_from_best_similarity(0.236) < 2.0
        # Out-of-domain controls measured <= 0.211 -> always flagged.
        assert ood_ratio_from_best_similarity(0.211) >= 2.0

    def test_real_model_integration_or_skip(self):
        pytest.importorskip("torch")
        pytest.importorskip("transformers")
        from civitas_vision.clip_classifier import CLIPZeroShotClassifier
        from PIL import Image

        classifier = CLIPZeroShotClassifier.load()
        if classifier is None:
            pytest.skip("CLIP checkpoint not available in this environment")
        probs = classifier.predict(Image.new("RGB", (224, 224), (90, 120, 150)))
        assert set(probs.probabilities) == set(REAL_MEDIA_CATEGORIES)
        assert probs.primary_category in REAL_MEDIA_CATEGORIES
        assert 0.0 <= probs.confidence <= 1.0
        assert probs.ood_ratio is not None and probs.ood_ratio > 0.0
        assert probs.secondary_label is None or isinstance(probs.secondary_label, str)
        assert any("zero-shot CLIP" in b for b in probs.basis)