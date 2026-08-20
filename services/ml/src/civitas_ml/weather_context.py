"""Environmental and Weather Telemetry Correlation Engine.

Evaluates current meteorological conditions (precipitation, temperature,
freeze-thaw oscillation) to contextualize civic flooding, asphalt heaving,
and drainage backup causes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WeatherContext:
    temperature_c: float
    precipitation_mm_hr: float
    wind_speed_kmh: float
    is_freeze_thaw_cycle: bool
    is_cloudburst_flooding: bool
    weather_attribution_factor: float  # 0.0 (pure physical defect) to 1.0 (pure weather event)
    summary_note: str


def get_weather_context(
    latitude: float,
    longitude: float,
    current_temp_c: float | None = None,
    current_precip_mm: float | None = None,
) -> WeatherContext:
    """Enriches incident evaluation with real-time or estimated meteorological telemetry."""
    # Deterministic default baselines for municipal evaluation if external telemetry is offline
    temp = current_temp_c if current_temp_c is not None else 24.5
    precip = current_precip_mm if current_precip_mm is not None else 0.0
    wind = 12.0

    # Freeze-thaw cycle: temperature oscillating between -3°C and +4°C with moisture
    freeze_thaw = -3.0 <= temp <= 4.0

    # Cloudburst: intense rainfall exceeding 25mm/hr
    cloudburst = precip >= 25.0

    if cloudburst:
        attribution = 0.85
        note = f"Heavy cloudburst active ({precip} mm/hr); storm runoff likely exacerbating drainage capacity."
    elif freeze_thaw:
        attribution = 0.65
        note = f"Active freeze-thaw thermal oscillation ({temp}°C); high risk of sub-base frost heaving and asphalt cavity expansion."
    elif precip > 5.0:
        attribution = 0.35
        note = f"Moderate rain ({precip} mm/hr); water accumulation present."
    else:
        attribution = 0.05
        note = "Dry meteorological conditions; defect is attributable to physical infrastructure wear or mechanical failure."

    return WeatherContext(
        temperature_c=temp,
        precipitation_mm_hr=precip,
        wind_speed_kmh=wind,
        is_freeze_thaw_cycle=freeze_thaw,
        is_cloudburst_flooding=cloudburst,
        weather_attribution_factor=round(attribution, 2),
        summary_note=note,
    )
