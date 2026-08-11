"""Tests for civitas_risk feature engineering."""

from civitas_geo.models import ExposureContext
from civitas_risk.contracts import RiskContext
from civitas_risk.features import (
    accessibility_signal,
    assemble_feature_vector,
    category_base_severity,
    electric_risk_signal,
    hospital_proximity_signal,
    longevity_signal,
    normalize_category,
    public_health_signal,
    repeated_report_signal,
    school_proximity_signal,
    traffic_signal,
    weather_escalation_signal,
)


def ctx(**kw) -> RiskContext:
    defaults = dict(report_id="r1", category="pothole", description="")
    defaults.update(kw)
    return RiskContext(**defaults)


def exposure(**kw) -> ExposureContext:
    defaults = dict(nearest_school_m=None, nearest_hospital_m=None,
                    junction_density_1km=0.0, nearest_waterbody_m=None,
                    pathway_proximity=False, traffic_exposure="moderate",
                    sources=[], inference=[])
    defaults.update(kw)
    return ExposureContext(**defaults)


def test_normalize_category_aliases():
    assert normalize_category("water leak") == "water_leak"
    assert normalize_category("Fallen Tree") == "fallen_tree"
    assert normalize_category("pothole") == "pothole"
    assert normalize_category("unknown thing") is None


def test_category_base_severity_table():
    base, _ = category_base_severity("streetlight")
    assert base == 0.35
    base2, _ = category_base_severity("fallen tree")
    assert base2 == 0.65
    unknown, _ = category_base_severity("mystery")
    assert unknown == 0.5


def test_electric_risk_from_text():
    out, basis = electric_risk_signal(ctx(description="broken pole with electric wire hanging"))
    assert out == 1.0
    assert "electric" in basis
    out2, _ = electric_risk_signal(ctx(description="just a hole in the road"))
    assert out2 == 0.0


def test_public_health_signal():
    assert public_health_signal(ctx(category="garbage"))[0] == 1.0
    assert public_health_signal(ctx(category="water_leak", rain_intensity_mm_h=40.0))[0] == 0.75
    assert public_health_signal(ctx(category="pothole"))[0] == 0.0


def test_school_proximity_tiers():
    assert school_proximity_signal(ctx(exposure=exposure(nearest_school_m=120.0)))[0] == 1.0
    assert school_proximity_signal(ctx(exposure=exposure(nearest_school_m=700.0)))[0] == 0.5
    assert school_proximity_signal(ctx(exposure=exposure(nearest_school_m=5000.0)))[0] == 0.0
    assert school_proximity_signal(ctx(exposure=None))[0] == 0.0


def test_hospital_proximity_tiers():
    assert hospital_proximity_signal(ctx(exposure=exposure(nearest_hospital_m=300.0)))[0] == 1.0
    assert hospital_proximity_signal(ctx(exposure=exposure(nearest_hospital_m=1500.0)))[0] == 0.5


def test_traffic_signal_mapping():
    assert traffic_signal(ctx(exposure=exposure(traffic_exposure="high")))[0] == 1.0
    assert traffic_signal(ctx(exposure=exposure(traffic_exposure="low")))[0] == 0.0
    assert traffic_signal(ctx(exposure=None))[0] == 0.0


def test_repeated_report_saturation():
    one, _ = repeated_report_signal(1)
    assert one == 0.0
    four, _ = repeated_report_signal(4)
    assert 0.6 < four < 0.9
    ten, _ = repeated_report_signal(10)
    assert ten > 0.95


def test_longevity_signal_saturates():
    fresh, _ = longevity_signal(1.0)
    assert fresh < 0.05
    two_weeks, _ = longevity_signal(336.0)
    assert 0.7 < two_weeks < 0.85
    month, _ = longevity_signal(30 * 24.0)
    assert month > 0.95


def test_weather_escalation_signal():
    assert weather_escalation_signal(ctx(category="water_leak", rain_intensity_mm_h=60.0))[0] == 1.0
    assert weather_escalation_signal(ctx(category="water_leak", rain_intensity_mm_h=25.0))[0] == 0.5
    assert weather_escalation_signal(ctx(category="water_leak", rain_intensity_mm_h=5.0))[0] == 0.0
    assert weather_escalation_signal(ctx(category="streetlight", rain_intensity_mm_h=60.0))[0] == 0.0
    assert weather_escalation_signal(ctx(category="water_leak", rain_intensity_mm_h=None))[0] == 0.0


def test_accessibility_signal():
    assert accessibility_signal(ctx(accessibility_blocked=True))[0] == 1.0
    exp = exposure(pathway_proximity=True)
    assert accessibility_signal(ctx(category="fallen_tree", exposure=exp))[0] == 0.8
    assert accessibility_signal(ctx(category="pothole", exposure=exp))[0] == 0.0


def test_feature_vector_complete_and_bounded():
    exp = exposure(nearest_school_m=100.0, nearest_hospital_m=400.0, traffic_exposure="high")
    f, p = assemble_feature_vector(ctx(category="fallen_tree", exposure=exp, description="live wire on tree", repeated_reports=5, open_hours=48.0, rain_intensity_mm_h=70.0))
    assert set(f.keys()) == set(p.keys())
    for feat, val in f.items():
        assert 0.0 <= val <= 1.0, feat
    assert f["electrical"] == 1.0
    assert f["school_proximity"] == 1.0