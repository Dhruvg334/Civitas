"""Phase 8 tests: resolution verification (the second ML moment).

Covers normal (the demo before/after pair -> PARTIALLY RESOLVED), boundary
(thresholds, coverage growth), and failure (unusable media, no measurable
hazard) behaviour. Unit tests build evidence at the evidence-string level;
integration tests run the real vision pipeline over the synthetic corpus
(flow variant -> standing variant is exactly the user story: "no active
water flow BUT standing water remains").

Pinned values from the synthetic corpus (seed 7101): the flow variant
measures water coverage 0.481 with evidence ['standing water',
'water flowing across road']; the standing variant measures 0.491 with
evidence ['standing water'].
"""

import pytest
from pydantic import ValidationError

from civitas_resolution import (
    ResolutionEvidence,
    ResolutionModel,
    outcome_label,
)
from civitas_resolution.model import (
    COVERAGE_GROWTH_CONFLICT_RATIO,
    STANDING_WATER_EVIDENCE_MIN,
)
from civitas_vision.benchmark import gaussian_blur, make_image
from civitas_vision.detector import VisualIntelligencePipeline
from civitas_vision.features import extract_features


def evidence(
    incident_id="CL-018",
    stage="before",
    source="test",
    media_usable=True,
    rejection_basis=None,
    primary_category="water_leakage",
    observable_evidence=None,
    water_coverage=0.0,
):
    markers = ("water flowing across road", "active water flow")
    active = int(any(m in " ".join(observable_evidence or []) for m in markers))
    return ResolutionEvidence(
        incident_id=incident_id,
        stage=stage,
        source=source,
        media_usable=media_usable,
        rejection_basis=rejection_basis or [],
        primary_category=primary_category,
        observable_evidence=observable_evidence or [],
        active_water_flow=active,
        water_coverage=water_coverage,
    )


class TestFromEvidence:
    def test_flow_flag_derived_from_flowing_marker_only(self):
        flowing = ResolutionEvidence.from_evidence(
            "CL-018", "before", "citizen upload",
            primary_category="water_leakage",
            observable_evidence=("standing water", "water flowing across road"),
            water_coverage=0.48,
        )
        assert flowing.active_water_flow == 1

        dried = ResolutionEvidence.from_evidence(
            "CL-018", "after", "inspector upload",
            primary_category="water_leakage",
            observable_evidence=("standing water",),
            water_coverage=0.30,
        )
        assert dried.active_water_flow == 0

    def test_contract_validates(self):
        with pytest.raises(ValidationError):
            evidence(water_coverage=1.5)
        with pytest.raises(ValidationError):
            ResolutionEvidence(incident_id="x", stage="before", water_coverage=-0.1)


class TestResolutionModelUnit:
    def test_resolved_everything_gone(self):
        verdict = ResolutionModel().assess(
            evidence(observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.48),
            evidence(stage="after",
                     observable_evidence=(), water_coverage=0.03),
        )
        assert verdict.outcome == "resolved"
        assert outcome_label(verdict.outcome) == "RESOLVED"
        assert verdict.resolved_signals == 2
        assert verdict.total_signals == 2

    def test_partial_user_story(self):
        verdict = ResolutionModel().assess(
            evidence(observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.60),
            evidence(stage="after",
                     observable_evidence=("standing water",), water_coverage=0.30),
        )
        assert verdict.outcome == "partial"
        assert outcome_label(verdict.outcome) == "PARTIALLY RESOLVED"
        statuses = {r.factor: r.status for r in verdict.reasons}
        assert statuses["active water flow"] == "resolved"
        assert statuses["standing water / coverage"] == "partial"

    def test_conflicting_flow_never_stopped(self):
        verdict = ResolutionModel().assess(
            evidence(observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.48),
            evidence(stage="after",
                     observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.48),
        )
        assert verdict.outcome == "conflicting"
        assert any(r.status == "unchanged" for r in verdict.reasons)

    def test_conflicting_coverage_grew(self):
        before = evidence(observable_evidence=("standing water",), water_coverage=0.40)
        after = evidence(stage="after", observable_evidence=("standing water",),
                         water_coverage=0.40 * COVERAGE_GROWTH_CONFLICT_RATIO + 0.01)
        verdict = ResolutionModel().assess(before, after)
        assert verdict.outcome == "conflicting"
        assert any(r.status == "worsened" for r in verdict.reasons)

    def test_coverage_shrunk_but_present_is_partial_not_resolved(self):
        before = evidence(observable_evidence=("standing water",), water_coverage=0.60)
        after = evidence(stage="after", observable_evidence=("standing water",),
                         water_coverage=0.40 * COVERAGE_GROWTH_CONFLICT_RATIO)
        verdict = ResolutionModel().assess(before, after)
        assert verdict.outcome == "partial"

    def test_coverage_below_observable_minimum_is_resolved(self):
        before = evidence(observable_evidence=("standing water",), water_coverage=0.30)
        after = evidence(stage="after", observable_evidence=(), water_coverage=0.19)
        verdict = ResolutionModel().assess(before, after)
        assert verdict.outcome == "resolved"

    def test_after_media_rejected_is_unverifiable(self):
        verdict = ResolutionModel().assess(
            evidence(observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.48),
            evidence(stage="after", source="inspector upload", media_usable=False,
                     rejection_basis=["blurry: variance of Laplacian 0.0001 < 0.0010"]),
        )
        assert verdict.outcome == "unverifiable"
        assert any("inspector upload" in r.evidence for r in verdict.reasons)

    def test_before_has_no_measurable_hazard_is_unverifiable(self):
        verdict = ResolutionModel().assess(
            evidence(observable_evidence=(), water_coverage=0.03),
            evidence(stage="after", observable_evidence=(), water_coverage=0.03),
        )
        assert verdict.outcome == "unverifiable"

    def test_different_hazard_in_after_is_conflicting(self):
        verdict = ResolutionModel().assess(
            evidence(primary_category="water_leakage",
                     observable_evidence=("standing water", "water flowing across road"),
                     water_coverage=0.48),
            evidence(stage="after", primary_category="pothole_road_damage",
                     observable_evidence=("visible road cavity (pothole) with broken surface",),
                     water_coverage=0.0),
        )
        assert verdict.outcome == "conflicting"
        assert any(r.factor == "hazard type" for r in verdict.reasons)

    def test_after_clean_photo_with_unknown_category_is_resolved(self):
        verdict = ResolutionModel().assess(
            evidence(primary_category="pothole_road_damage",
                     observable_evidence=("visible road cavity (pothole) with broken surface",)),
            evidence(stage="after", primary_category=None, observable_evidence=()),
        )
        assert verdict.outcome == "resolved"

    def test_deterministic(self):
        model = ResolutionModel()
        before = evidence(observable_evidence=("standing water", "water flowing across road"),
                          water_coverage=0.48)
        after = evidence(stage="after", observable_evidence=("standing water",),
                         water_coverage=0.49)
        assert model.assess(before, after) == model.assess(before, after)

    def test_streetlight_binary_categories(self):
        before = evidence(primary_category="broken_streetlight",
                          observable_evidence=("dark scene with a localized bright bulb region",),
                          water_coverage=0.0)
        fixed = evidence(stage="after", primary_category="broken_streetlight",
                         observable_evidence=(), water_coverage=0.0)
        still = evidence(stage="after", primary_category="broken_streetlight",
                         observable_evidence=("dark scene with a localized bright bulb region",),
                         water_coverage=0.0)
        assert ResolutionModel().assess(before, fixed).outcome == "resolved"
        assert ResolutionModel().assess(before, still).outcome == "conflicting"

    def test_standing_threshold_constant_mirrors_vision_rule(self):
        assert STANDING_WATER_EVIDENCE_MIN == 0.20


class TestResolutionVisionIntegration:
    @pytest.fixture(scope="class")
    def before_after(self):
        vision = VisualIntelligencePipeline()
        flow_img = make_image("water_leakage", 7101, variant="flow")
        standing_img = make_image("water_leakage", 7101, variant="default")
        before = ResolutionEvidence.from_vision(
            "CL-018", "before", "citizen upload (R1)", vision.analyze_image(flow_img),
            water_coverage=extract_features(flow_img)["blue_smooth_share"],
        )
        after = ResolutionEvidence.from_vision(
            "CL-018", "after", "inspector upload", vision.analyze_image(standing_img),
            water_coverage=extract_features(standing_img)["blue_smooth_share"],
        )
        return before, after

    def test_flow_variant_shows_active_flow(self, before_after):
        before, _ = before_after
        assert before.active_water_flow == 1
        assert "water flowing across road" in before.observable_evidence
        assert before.water_coverage == pytest.approx(0.481, abs=0.005)

    def test_standing_variant_keeps_puddle_only(self, before_after):
        _, after = before_after
        assert after.active_water_flow == 0
        assert "standing water" in after.observable_evidence
        assert "water flowing across road" not in after.observable_evidence
        assert after.water_coverage == pytest.approx(0.491, abs=0.005)

    def test_demo_pair_is_partially_resolved(self, before_after):
        before, after = before_after
        verdict = ResolutionModel().assess(before, after)
        assert verdict.outcome == "partial"
        statuses = {r.factor: r.status for r in verdict.reasons}
        assert statuses["active water flow"] == "resolved"
        assert statuses["standing water / coverage"] == "partial"
        assert verdict.resolved_signals == 1
        assert verdict.total_signals == 2

    def test_blurred_after_photo_is_unverifiable(self):
        vision = VisualIntelligencePipeline()
        flow_img = make_image("water_leakage", 7101, variant="flow")
        before = ResolutionEvidence.from_vision(
            "CL-018", "before", "citizen upload (R1)", vision.analyze_image(flow_img),
            water_coverage=extract_features(flow_img)["blue_smooth_share"],
        )
        blurred = gaussian_blur(make_image("water_leakage", 7101, variant="default"), radius=4)
        after = ResolutionEvidence.from_vision(
            "CL-018", "after", "inspector upload (blurry)", vision.analyze_image(blurred),
            water_coverage=extract_features(blurred)["blue_smooth_share"],
        )
        assert after.media_usable is False
        assert ResolutionModel().assess(before, after).outcome == "unverifiable"

    def test_fresh_flow_photo_is_conflicting(self):
        vision = VisualIntelligencePipeline()
        flow_img = make_image("water_leakage", 7101, variant="flow")
        before = ResolutionEvidence.from_vision(
            "CL-018", "before", "citizen upload (R1)", vision.analyze_image(flow_img),
            water_coverage=extract_features(flow_img)["blue_smooth_share"],
        )
        again = ResolutionEvidence.from_vision(
            "CL-018", "after", "inspector upload", vision.analyze_image(flow_img),
            water_coverage=extract_features(flow_img)["blue_smooth_share"],
        )
        verdict = ResolutionModel().assess(before, again)
        assert verdict.outcome == "conflicting"
        assert any(r.status == "unchanged" for r in verdict.reasons)

    def test_other_hazard_photo_is_conflicting(self):
        vision = VisualIntelligencePipeline()
        flow_img = make_image("water_leakage", 7101, variant="flow")
        before = ResolutionEvidence.from_vision(
            "CL-018", "before", "citizen upload (R1)", vision.analyze_image(flow_img),
            water_coverage=extract_features(flow_img)["blue_smooth_share"],
        )
        pothole_img = make_image("pothole_road_damage", 2200)
        after = ResolutionEvidence.from_vision(
            "CL-018", "after", "inspector upload", vision.analyze_image(pothole_img),
            water_coverage=extract_features(pothole_img)["blue_smooth_share"],
        )
        assert after.primary_category == "pothole_road_damage"
        verdict = ResolutionModel().assess(before, after)
        assert verdict.outcome == "conflicting"
        assert any(r.factor == "hazard type" for r in verdict.reasons)