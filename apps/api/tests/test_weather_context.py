"""Unit tests for environmental and weather telemetry correlation engine."""

from civitas_ml.weather_context import get_weather_context


def test_dry_weather_context():
    w = get_weather_context(20.29614, 85.82451, current_temp_c=28.0, current_precip_mm=0.0)
    assert w.is_cloudburst_flooding is False
    assert w.is_freeze_thaw_cycle is False
    assert w.weather_attribution_factor <= 0.10
    assert "Dry meteorological" in w.summary_note


def test_freeze_thaw_cycle_detection():
    w = get_weather_context(40.7128, -74.0060, current_temp_c=-1.5, current_precip_mm=2.0)
    assert w.is_freeze_thaw_cycle is True
    assert w.is_cloudburst_flooding is False
    assert w.weather_attribution_factor >= 0.50
    assert "freeze-thaw" in w.summary_note


def test_cloudburst_flooding_detection():
    w = get_weather_context(19.0760, 72.8777, current_temp_c=26.0, current_precip_mm=45.0)
    assert w.is_cloudburst_flooding is True
    assert w.weather_attribution_factor >= 0.80
    assert "cloudburst" in w.summary_note
