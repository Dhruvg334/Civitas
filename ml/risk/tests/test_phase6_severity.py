"""Phase 6 tests: incident severity feature engineering + the two models.

Covers normal (the demo water-leak incident), boundary (level thresholds,
caps) and failure (missing evidence) behaviour. The canonical demo feature
set is deliberately fixed so the expected numbers are pinned values:
water-leak incident, active flow, covered road, school 37 m, moderate
traffic, 3 reports, 1.2 h -> severity 78 HIGH.
"""

from datetime import datetime, timezone

import pytest
from civitas_geo.models import ExposureContext
from civitas_risk import (
    ConsolidatedIncident,
    IncidentFeatures,
    IncidentVisualEvidence,
    PriorityContext,
    PriorityModel,
    SeverityModel,
    build_incident_features,
    build_priority_features,
    priority_level_for,
)
from civitas_risk.severity_model import severity_level_for
from pydantic import ValidationError

DEMO_EXPOSURE = ExposureContext(
    nearest_school_m=37.0,
    nearest_hospital_m=583.5,
    junction_density_1km=0.637,
    nearest_waterbody_m=None,
    pathway_proximity=False,
    traffic_exposure="moderate",
    sources=["landmark-index"],
    inference=[],
)

DEMO_VISUAL = IncidentVisualEvidence(
    primary_category="water_leakage",
    observed_evidence=["water flowing across road", "standing water"],
    active_water_flow=1,
    water_coverage=0.49,
)


def demo_incident(**kw) -> ConsolidatedIncident:
    defaults = dict(
        incident_id="CL-018",
        category="water leak",
        visual=DEMO_VISUAL,
        exposure=DEMO_EXPOSURE,
        report_count=3,
        duration_hours=1.25,
        rain_intensity_mm_h=None,
    )
    defaults.update(kw)
    return ConsolidatedIncident(**defaults)


def demo_features() -> IncidentFeatures:
    return build_incident_features(demo_incident())


class TestIncidentFeatureEngineering:
    def test_demo_features_are_typed_and_complete(self):
        features = demo_features()
        assert features.incident_id == "CL-018"
        assert features.active_water_flow == 1
        assert features.water_coverage == pytest.approx(0.49)
        assert features.school_distance_m == pytest.approx(37.0)
        assert features.hospital_distance_m == pytest.approx(583.5)
        assert features.traffic_exposure == "moderate"
        assert features.report_count == 3
        assert features.duration_hours == pytest.approx(1.25)

    def test_every_feature_has_provenance(self):
        features = demo_features()
        for key in ("category", "active_water_flow", "water_coverage",
                    "school_distance_m", "traffic_exposure", "report_count",
                    "duration_hours"):
            assert features.provenance[key], f"missing provenance for {key}"
        assert "school at" in features.provenance["school_distance_m"]

    def test_visual_evidence_strings_derive_flow_flag(self):
        visual = IncidentVisualEvidence.from_evidence(
            "water_leakage", ["standing water", "water flowing across road"]
        )
        assert visual.active_water_flow == 1
        quiet = IncidentVisualEvidence.from_evidence("pothole_road_damage", ["cavity observed"])
        assert quiet.active_water_flow == 0
        assert quiet.water_coverage == 0.0

    def test_no_visual_no_exposure_records_absence(self):
        features = build_incident_features(
            ConsolidatedIncident(incident_id="CL-001", category="streetlight")
        )
        assert features.active_water_flow == 0
        assert features.water_coverage == 0.0
        assert features.school_distance_m is None
        assert features.traffic_exposure is None
        assert "no visual evidence recorded" in features.provenance["active_water_flow"]
        assert "no geospatial exposure computed" in features.provenance["school_distance_m"]

    def test_contract_rejects_impossible_inputs(self):
        with pytest.raises(ValidationError):
            ConsolidatedIncident(incident_id="x", category="water leak", report_count=0)
        with pytest.raises(ValidationError):
            ConsolidatedIncident(incident_id="x", category="water leak", duration_hours=-1)
        with pytest.raises(ValidationError):
            IncidentVisualEvidence(active_water_flow=2)


class TestSeverityModel:
    def test_demo_scenario_scores_78_high(self):
        assessment = SeverityModel().assess(demo_features())
        assert assessment.score == 78
        assert assessment.level == "high"
        factor_names = [c.factor for c in assessment.contributing_factors]
        for expected in ("active road flooding", "slip hazard", "significant affected area",
                         "near school", "crowd corroboration", "protracted exposure"):
            assert expected in factor_names

    def test_factor_evidence_lines_cite_real_values(self):
        assessment = SeverityModel().assess(demo_features())
        by_name = {c.factor: c.evidence for c in assessment.contributing_factors}
        assert "37 m" in by_name["near school"]
        assert "0.49" in by_name["significant affected area"]
        assert "3" in by_name["crowd corroboration"]

    def test_point_total_is_explainable(self):
        assessment = SeverityModel().assess(demo_features())
        assert sum(c.points for c in assessment.contributing_factors) == 100

    def test_bare_incident_gets_base_only(self):
        features = build_incident_features(
            ConsolidatedIncident(incident_id="CL-002", category="streetlight")
        )
        assessment = SeverityModel().assess(features)
        assert assessment.score == 41  # 35 base points after the squash
        assert assessment.level == "medium"
        assert len(assessment.contributing_factors) == 1

    def test_unknown_category_uses_neutral_base(self):
        features = build_incident_features(
            ConsolidatedIncident(incident_id="CL-003", category="mystery incident")
        )
        assert SeverityModel().assess(features).score == 49  # 45 neutral points after the squash

    def test_level_band_boundaries(self):
        assert severity_level_for(34) == "low"
        assert severity_level_for(35) == "medium"
        assert severity_level_for(59) == "medium"
        assert severity_level_for(60) == "high"
        assert severity_level_for(79) == "high"
        assert severity_level_for(80) == "critical"

    def test_score_never_exceeds_100(self):
        features = build_incident_features(demo_incident(
            report_count=99, duration_hours=96.0,
            rain_intensity_mm_h=99.0,
        ))
        assert SeverityModel().assess(features).score <= 100

    def test_slip_hazard_requires_road_traffic(self):
        quiet_traffic = IncidentFeatures(
            incident_id="x", category="water leak", active_water_flow=1,
            water_coverage=0.49, school_distance_m=37.0,
            hospital_distance_m=None, traffic_exposure="low",
            junction_density_1km=0.0, report_count=1, duration_hours=0.0,
        )
        assessment = SeverityModel().assess(quiet_traffic)
        names = [c.factor for c in assessment.contributing_factors]
        assert "slip hazard" not in names
        assert "heavy traffic exposure" not in names
        assert "moderate traffic exposure" not in names


class TestPriorityModel:
    def test_priority_is_a_separate_decision(self):
        features = demo_features()
        severity = SeverityModel().assess(features)
        priority = PriorityModel().assess(
            build_priority_features(PriorityContext(
                incident=demo_incident(),
                severity_score=severity.score,
                population_density_proxy=0.255,
                nearby_density_norm=0.10,
                current_time=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            ))
        )
        assert priority.score != severity.score
        assert priority.level == "high"  # 10-signal model on the demo incident
        assert priority.severity_score == severity.score
        names = [r.factor for r in priority.reasons]
        assert "incident severity" in names
        assert "school nearby" in names
        assert "multiple independent reports" in names

    def test_priority_escalates_with_severity(self):
        model = PriorityModel()

        def assess(severity: int) -> int:
            return model.assess(build_priority_features(PriorityContext(
                incident=demo_incident(),
                severity_score=severity,
                population_density_proxy=0.255,
                nearby_density_norm=0.10,
                current_time=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            ))).score

        assert assess(78) > assess(41)

    def test_level_boundaries(self):
        assert priority_level_for(39) == "low"
        assert priority_level_for(40) == "medium"
        assert priority_level_for(59) == "medium"
        assert priority_level_for(60) == "high"
        assert priority_level_for(79) == "high"
        assert priority_level_for(80) == "critical"

    def test_priority_deterministic(self):
        context = PriorityContext(
            incident=demo_incident(), severity_score=78,
            population_density_proxy=0.255, nearby_density_norm=0.10,
            current_time=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        )
        a = PriorityModel().assess(build_priority_features(context))
        b = PriorityModel().assess(build_priority_features(context))
        assert a == b

    def test_urgency_reflects_school_distance(self):
        model = PriorityModel()

        def assess_for(school_m: float) -> int:
            incident = demo_incident(exposure=DEMO_EXPOSURE.model_copy(
                update={"nearest_school_m": school_m}
            ))
            return model.assess(build_priority_features(PriorityContext(
                incident=incident,
                severity_score=78,
                population_density_proxy=0.255,
                nearby_density_norm=0.10,
                current_time=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
            ))).score

        assert assess_for(37.0) > assess_for(5000.0)

    def test_reason_points_are_consistent_with_score(self):
        context = PriorityContext(
            incident=demo_incident(), severity_score=78,
            population_density_proxy=0.255, nearby_density_norm=0.10,
            current_time=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
        )
        priority = PriorityModel().assess(build_priority_features(context))
        assert priority.score - sum(r.points for r in priority.reasons) <= 2