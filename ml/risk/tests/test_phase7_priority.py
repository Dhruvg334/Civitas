"""Phase 7 tests: priority feature engineering + the 10-signal priority model.

The demo school-gate flood is the canonical scenario: severity 78, school at
37 m, hospital 584 m, moderate traffic, population proxy 0.255, 3 reports,
1.2 h, density 0.10, water-leak category, noon — a pinned priority of 63
(HIGH). The worst-case saturation corner lands in the CRITICAL band, the
state the product must never auto-route without human review.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from civitas_geo.models import ExposureContext
from civitas_risk import (
    PriorityContext,
    PriorityModel,
    build_priority_features,
    category_urgency_signal,
    priority_level_for,
)
from civitas_risk.incident_features import ConsolidatedIncident, IncidentVisualEvidence

NOON = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)

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

VISUAL = IncidentVisualEvidence(
    primary_category="water_leakage",
    observed_evidence=["water flowing across road"],
    active_water_flow=1,
    water_coverage=0.49,
)


def demo_context(**kw) -> PriorityContext:
    defaults = dict(
        incident=ConsolidatedIncident(
            incident_id="CL-018",
            category="water leak",
            visual=VISUAL,
            exposure=DEMO_EXPOSURE,
            report_count=3,
            duration_hours=1.25,
        ),
        severity_score=78,
        population_density_proxy=0.255,
        nearby_density_norm=0.10,
        current_time=NOON,
    )
    defaults.update(kw)
    return PriorityContext(**defaults)


class TestPriorityFeatureEngineering:
    def test_ten_signals_are_typed_with_provenance(self):
        features = build_priority_features(demo_context())
        assert features.severity_score == 78
        assert features.school_proximity == pytest.approx(1.0)
        assert features.hospital_proximity == pytest.approx(0.5)
        assert features.traffic_exposure == pytest.approx(0.5)
        assert features.population_exposure == pytest.approx(0.255, abs=1e-3)
        assert features.repeated_reports == pytest.approx(0.632, abs=1e-3)
        assert features.incident_duration == pytest.approx(0.052, abs=1e-3)
        assert features.nearby_density == pytest.approx(0.10)
        assert features.category_urgency == pytest.approx(0.6)
        assert features.time_sensitivity == pytest.approx(0.8)
        for key in ("school_proximity", "traffic_exposure", "repeated_reports",
                    "time_sensitivity", "nearby_density"):
            assert features.provenance[key]

    def test_missing_geo_inputs_record_absence_not_guesses(self):
        features = build_priority_features(PriorityContext(
            incident=ConsolidatedIncident(incident_id="CL-001", category="streetlight"),
            severity_score=35,
        ))
        assert features.school_proximity == 0.0
        assert features.hospital_proximity == 0.0
        assert features.traffic_exposure == 0.0
        assert features.population_exposure == 0.0
        assert features.time_sensitivity == 0.5  # unknown hour -> neutral
        assert "no geospatial exposure computed" in features.provenance["school_proximity"]
        assert "neutral" in features.provenance["time_sensitivity"]

    def test_repeated_report_signal_saturates(self):
        features = build_priority_features(demo_context(
            incident=demo_context().incident.model_copy(update={"report_count": 4})
        ))
        near = build_priority_features(demo_context(
            incident=demo_context().incident.model_copy(update={"report_count": 8})
        ))
        assert 0.95 <= near.repeated_reports <= 1.0
        assert near.repeated_reports > features.repeated_reports

    def test_category_urgency_table(self):
        assert category_urgency_signal("garbage overflow")[0] == 0.8
        assert category_urgency_signal("water leak")[0] == 0.6
        assert category_urgency_signal("streetlight")[0] == 0.2
        signal, basis = category_urgency_signal("mystery")
        assert signal == 0.4
        assert "neutral" in basis

    def test_time_sensitivity_day_vs_night(self):
        day = build_priority_features(demo_context(current_time=NOON))  # 12:00
        night = build_priority_features(demo_context(
            current_time=datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc)
        ))
        assert day.time_sensitivity == 0.8
        assert night.time_sensitivity == 0.2

    def test_rain_escalates_time_sensitivity(self):
        rainy = demo_context(incident=demo_context().incident.model_copy(
            update={"rain_intensity_mm_h": 25.0}
        ))
        assert build_priority_features(rainy).time_sensitivity == 1.0

    def test_contract_validates(self):
        with pytest.raises(ValidationError):
            PriorityContext(incident=demo_context().incident, severity_score=150)
        with pytest.raises(ValidationError):
            demo_context(population_density_proxy=-0.1)


class TestPriorityModel:
    def test_demo_scenario_scores_63_high(self):
        priority = PriorityModel().assess(build_priority_features(demo_context()))
        assert priority.score == 63
        assert priority.level == "high"
        names = [r.factor for r in priority.reasons]
        for expected in ("incident severity", "school nearby", "multiple independent reports",
                         "traffic exposure", "category urgency", "time sensitivity"):
            assert expected in names

    def test_reason_evidence_cites_real_values(self):
        priority = PriorityModel().assess(build_priority_features(demo_context()))
        by_name = {r.factor: r.evidence for r in priority.reasons}
        assert "37 m" in by_name["school nearby"]
        assert "3 merged report(s)" in by_name["multiple independent reports"]

    def test_saturated_incident_hits_critical(self):
        features = build_priority_features(PriorityContext(
            incident=ConsolidatedIncident(
                incident_id="CL-999",
                category="garbage overflow",
                exposure=DEMO_EXPOSURE.model_copy(update={
                    "nearest_school_m": 20.0, "nearest_hospital_m": 120.0,
                    "traffic_exposure": "high", "junction_density_1km": 4.2,
                }),
                report_count=8,
                duration_hours=72.0,
                rain_intensity_mm_h=50.0,
            ),
            severity_score=90,
            population_density_proxy=0.8,
            nearby_density_norm=0.85,
            current_time=NOON,
        ))
        priority = PriorityModel().assess(features)
        assert priority.score >= 85
        assert priority.level == "critical"
        names = [r.factor for r in priority.reasons]
        assert "school nearby" in names and "high traffic" in " ".join(names) or "traffic exposure" in names
        assert "multiple independent reports" in names

    def test_weights_sum_to_one(self):
        model = PriorityModel()
        assert abs(sum(model.WEIGHTS.values()) - 1.0) < 1e-6

    def test_score_is_weighted_sum(self):
        features = build_priority_features(demo_context())
        priority = PriorityModel().assess(features)
        model = PriorityModel()
        expected = 100.0 * sum(
            model.WEIGHTS[k] * s for k, s in {
                "severity_score": features.severity_score / 100.0,
                "school_proximity": features.school_proximity,
                "hospital_proximity": features.hospital_proximity,
                "traffic_exposure": features.traffic_exposure,
                "population_exposure": features.population_exposure,
                "repeated_reports": features.repeated_reports,
                "incident_duration": features.incident_duration,
                "nearby_density": features.nearby_density,
                "category_urgency": features.category_urgency,
                "time_sensitivity": features.time_sensitivity,
            }.items()
        )
        assert priority.score == round(expected)

    def test_level_band_boundaries(self):
        assert priority_level_for(39) == "low"
        assert priority_level_for(40) == "medium"
        assert priority_level_for(59) == "medium"
        assert priority_level_for(60) == "high"
        assert priority_level_for(79) == "high"
        assert priority_level_for(80) == "critical"

    def test_deterministic(self):
        a = PriorityModel().assess(build_priority_features(demo_context()))
        b = PriorityModel().assess(build_priority_features(demo_context()))
        assert a == b

    def test_reason_points_sum_approximates_score(self):
        priority = PriorityModel().assess(build_priority_features(demo_context()))
        assert priority.score - sum(r.points for r in priority.reasons) <= 2