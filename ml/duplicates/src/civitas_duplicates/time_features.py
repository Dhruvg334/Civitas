"""Temporal proximity signals for duplicate reports."""

from __future__ import annotations

import math
from datetime import datetime, timezone


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def time_delta_hours(a: datetime, b: datetime) -> float:
    """Absolute difference in hours between two report times."""
    return abs((_as_utc(b) - _as_utc(a)).total_seconds()) / 3600.0


def time_similarity(
    a: datetime, b: datetime, sigma_hours: float = 24.0
) -> tuple[float, float]:
    """(similarity, delta_hours). Same-incident reports usually arrive in a
    short burst (hours to days); RBF decay with a 24 h half-life."""
    dh = time_delta_hours(a, b)
    sim = math.exp(-((dh / sigma_hours) ** 2))
    return sim, dh


def within_burst_window_hours(delta_h: float, window_h: float = 72.0) -> bool:
    """Burst gate: reports further apart in time are usually distinct."""
    return delta_h <= window_h