"""Unit tests for automated defect metric sizing and PCI distress rating."""

from civitas_ml.defect_metric import evaluate_defect_metrics


def test_evaluate_pothole_metrics():
    res = evaluate_defect_metrics(
        category="pothole_road_damage",
        visual_features=["deep_asphalt_cavity", "severe_fissure"],
        bounding_box_ratio=0.35,
    )
    assert res.estimated_area_cm2 >= 800.0
    assert res.estimated_depth_mm >= 70.0
    assert res.distress_level == "high"
    assert res.pci_deduction_score >= 40.0
    assert res.infrastructure_health_index <= 60.0
    assert "Hot-Mix" in res.recommended_patch_type


def test_evaluate_water_leak_metrics():
    res = evaluate_defect_metrics(
        category="water_leakage",
        visual_features=["water_main_burst", "standing_water_ponding"],
        bounding_box_ratio=0.45,
    )
    assert res.distress_level == "critical"
    assert res.estimated_depth_mm >= 100.0
    assert res.pci_deduction_score >= 50.0
    assert "Ductile Iron" in res.recommended_patch_type


def test_evaluate_minor_defect():
    res = evaluate_defect_metrics(
        category="broken_streetlight",
        visual_features=["non_functional_bulb"],
    )
    assert res.distress_level == "low"
    assert res.pci_deduction_score == 10.0
    assert res.infrastructure_health_index == 90.0


def test_evaluate_defect_empty_features_and_zero_bbox():
    res = evaluate_defect_metrics(
        category="general_hazard",
        visual_features=None,
        bounding_box_ratio=0.0,
    )
    assert res.estimated_area_cm2 >= 100.0
    assert res.estimated_depth_mm >= 20.0
    assert 0.0 <= res.infrastructure_health_index <= 100.0


def test_evaluate_defect_extreme_distress_bounds():
    res = evaluate_defect_metrics(
        category="water_leakage",
        visual_features=["burst", "flooding", "massive"],
        bounding_box_ratio=1.0,
    )
    assert 0.0 <= res.infrastructure_health_index <= 100.0
    assert res.pci_deduction_score >= 50.0
