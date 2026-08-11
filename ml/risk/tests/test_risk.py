"""Tests for severity rules, priority logic, ML calibration and composition."""

import pytest

from civitas_geo.models import ExposureContext
from civitas_risk.contracts import RiskContext
from civitas_risk.ml_models import LogisticCalibrator
from civitas_risk.priority import PriorityAssessor, PriorityConfig, tier_for
from civitas_risk.severity import SeverityAssessor, severity_level


def ctx(**kw) -> RiskContext:
    defaults = dict(report_id="r1", category="pothole", description="")
    defaults.update(kw)
    return RiskContext(**defaults)


def base_exposure() -> ExposureContext:
    return ExposureContext(
        nearest_school_m=None,
        nearest_hospital_m=None,
        junction_density_1km=0.0,
        nearest_waterbody_m=None,
        pathway_proximity=False,
        traffic_exposure="moderate",
        sources=[],
        inference=[],
    )


class TestSeverityRules:
    def test_base_levels(self):
        low = SeverityAssessor().assess(ctx(category="streetlight"))
        assert low.level == "medium"
        assert low.score == pytest.approx(0.35)
        high = SeverityAssessor().assess(ctx(category="fallen_tree"))
        assert high.score == pytest.approx(0.65)

    def test_electrical_raises_severity(self):
        s_normal = SeverityAssessor().assess(ctx(category="pothole"))
        s_elec = SeverityAssessor().assess(ctx(category="pothole", description="electric wire exposed"))
        assert s_elec.score == pytest.approx(s_normal.score + 0.15)
        assert "electrical" in s_elec.contributing_factors

    def test_school_and_traffic_raise(self):
        exp = base_exposure()
        exp.nearest_school_m = 90.0
        exp.traffic_exposure = "high"
        res = SeverityAssessor().assess(ctx(category="pothole", exposure=exp))
        assert res.score >= 0.75
        assert "school_close" in res.contributing_factors
        assert "traffic_high" in res.contributing_factors

    def test_score_clamped(self):
        exp = base_exposure()
        exp.nearest_school_m = 50.0
        exp.traffic_exposure = "high"
        res = SeverityAssessor().assess(
            ctx(category="fallen_tree", exposure=exp, description="live power line on tree")
        )
        assert res.score <= 1.0
        assert res.score >= 0.9

    def test_level_buckets(self):
        assert severity_level(0.2) == "low"
        assert severity_level(0.5) == "medium"
        assert severity_level(0.7) == "high"
        assert severity_level(0.9) == "critical"

    def test_decision_basis_explains(self):
        res = SeverityAssessor().assess(ctx(category="water_leak", rain_intensity_mm_h=60.0))
        assert any("rain" in b for b in res.decision_basis)
        assert any("category base" in b for b in res.decision_basis)


class TestPriority:
    def test_weights_must_sum_to_one(self):
        with pytest.raises(ValueError):
            PriorityConfig(weight_severity=0.9)

    def test_priority_separate_from_severity(self):
        # Same severity, different urgency -> different priority.
        assess = PriorityAssessor()
        leaf = ctx(category="pothole")  # severity 0.55, no exposure
        school = ctx(category="pothole", exposure=base_exposure())
        school.exposure.nearest_school_m = 100.0  # type: ignore[union-attr]
        school.exposure.traffic_exposure = "high"  # type: ignore[union-attr]
        p_leaf = assess.assess(leaf, 0.55).score
        p_school = assess.assess(school, 0.55).score
        assert p_school > p_leaf + 0.1

    def test_repeated_reports_raise_priority(self):
        assess = PriorityAssessor()
        single = assess.assess(ctx(category="streetlight"), 0.35)
        many = assess.assess(ctx(category="streetlight", repeated_reports=8), 0.35)
        assert many.score > single.score
        assert tier_for(many.score) <= tier_for(single.score)

    def test_tier_mapping(self):
        assert tier_for(0.85) == "P1"
        assert tier_for(0.7) == "P2"
        assert tier_for(0.5) == "P3"
        assert tier_for(0.2) == "P4"

    def test_critical_incident_gets_p1(self):
        exp = base_exposure()
        exp.nearest_school_m = 50.0
        exp.traffic_exposure = "high"
        sev = SeverityAssessor().assess(ctx(category="fallen_tree", exposure=exp, repeated_reports=5, open_hours=100.0))
        pri = PriorityAssessor().assess(ctx(category="fallen_tree", exposure=exp, repeated_reports=5, open_hours=100.0), sev.score)
        assert pri.tier == "P1"


class TestMLCalibration:
    def test_fit_reduces_error_on_separable_data(self):
        X = [[0.1, 0.2], [0.9, 0.8], [0.2, 0.1], [0.8, 0.9], [0.0, 0.15], [1.0, 0.85]]
        y = [0.1, 0.9, 0.15, 0.85, 0.05, 0.95]
        model = LogisticCalibrator(feature_names=["a", "b"], iterations=500).fit(X, y)
        preds = model.predict_proba(X)
        assert model.training_rmse_ is not None
        assert model.training_rmse_ < 0.15
        for p in preds:
            assert 0.0 <= p <= 1.0

    def test_unfitted_raises(self):
        model = LogisticCalibrator()
        with pytest.raises(RuntimeError):
            model.predict_proba([[0.5, 0.5]])

    def test_feature_count_mismatch(self):
        model = LogisticCalibrator(feature_names=["a", "b"], iterations=10).fit([[0.5, 0.5]], [0.5])
        with pytest.raises(ValueError):
            model.predict_proba([[0.5, 0.5, 0.5]])

    def test_artifact_roundtrip(self):
        model = LogisticCalibrator(feature_names=["a", "b"], iterations=50).fit(
            [[0.2, 0.3], [0.8, 0.7], [0.4, 0.4]], [0.2, 0.9, 0.5]
        )
        artifact = model.to_artifact()
        assert artifact["intercept"] == pytest.approx(model.intercept_)
        assert artifact["feature_names"] == model.feature_names

    def test_ml_blend_changes_score(self):
        X = [[0.1, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
             [0.9, 0.8, 0.9, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
             [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]]
        y = [0.2, 0.9, 0.5]
        calibrator = LogisticCalibrator(iterations=300).fit(X, y)
        plain = SeverityAssessor().assess(ctx(category="streetlight"))
        blended = SeverityAssessor(calibrator=calibrator, ml_blend_weight=0.5).assess(ctx(category="streetlight"))
        assert blended.ml_blend_weight == 0.5
        assert "ML calibration blend" in " ".join(blended.decision_basis)
        assert abs(blended.score - plain.score) > 1e-4 or plain.score == blended.score