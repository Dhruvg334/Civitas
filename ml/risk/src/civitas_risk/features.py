"""Engineered severity/priority features.

Every feature is normalized to [0,1] with an explicit provenance chain so
downstream logic can cite "near school (120 m)" instead of a bare number.
Feature design follows the ensemble-feature approach of the reference
GeoGPT project: many small, interpretable signals that combine into
calibrated risk.
"""

from __future__ import annotations

import math
import re

from civitas_risk.contracts import CATEGORIES, RiskContext

BASE_SEVERITY: dict[str, float] = {
    "pothole": 0.55,
    "water_leak": 0.50,
    "garbage": 0.45,
    "streetlight": 0.35,
    "fallen_tree": 0.65,
}

CATEGORY_ALIASES: dict[str, str] = {
    "water leak": "water_leak",
    "waterlogging": "water_leak",
    "flooding": "water_leak",
    "potholes": "pothole",
    "garbage overflow": "garbage",
    "waste": "garbage",
    "street light": "streetlight",
    "streetlights": "streetlight",
    "fallen tree": "fallen_tree",
    "tree": "fallen_tree",
    "blocked pathway": "fallen_tree",
    "road damage": "pothole",
}


def normalize_category(category: str | None) -> str | None:
    """Map citizen/vision category spellings onto canonical CATEGORIES."""
    if not category:
        return None
    key = category.strip().lower()
    if key in CATEGORIES:
        return key
    return CATEGORY_ALIASES.get(key)


UNKNOWN_CATEGORY_BASE = 0.5


def category_base_severity(category: str | None) -> tuple[float, str]:
    """Base severity for the canonical category (observable, static table)."""
    canon = normalize_category(category)
    if canon is None:
        return UNKNOWN_CATEGORY_BASE, "unknown category -> neutral base 0.50"
    return BASE_SEVERITY[canon], f"category base severity {BASE_SEVERITY[canon]:.2f} ({canon})"


def electric_risk_from_text(description: str) -> tuple[bool, str]:
    """Electrical hazard markers from free text (labelled inference)."""
    text = description.lower()
    markers = ["electric", "wire", "cable", "spark", "power line", "transformer", "pole"]
    hits = [m for m in markers if m in text]
    if not hits:
        return False, "no electrical markers in text"
    return True, f"electrical markers found: {', '.join(hits)}"


def electric_risk_signal(
    ctx: RiskContext,
    explicit: bool | None = None,
) -> tuple[float, str]:
    """1.0 when electrical risk present; text markers are labelled inference."""
    if explicit is None:
        explicit = ctx.electrical_risk_text
    from_text, basis = electric_risk_from_text(ctx.description)
    present = explicit or from_text
    if present:
        return 1.0, basis + (" / explicit flag" if explicit else "")
    return 0.0, "no electrical risk signal"


def public_health_signal(ctx: RiskContext) -> tuple[float, str]:
    """Overflowing garbage or water contamination risk."""
    canon = normalize_category(ctx.category)
    if canon == "garbage":
        return 1.0, "category garbage overflow -> public health exposure"
    if canon == "water_leak" and (ctx.rain_intensity_mm_h or 0.0) >= 20.0:
        return 0.75, "water + heavy rain -> flooding/public health risk"
    if canon == "water_leak":
        return 0.4, "water leak -> standing water / contamination potential"
    return 0.0, "no direct public health exposure"


def accessibility_signal(ctx: RiskContext) -> tuple[float, str]:
    """Blocked pedestrian/emergency pathway."""
    canon = normalize_category(ctx.category)
    if ctx.accessibility_blocked:
        return 1.0, "explicit blocked-pathway flag"
    if canon == "fallen_tree" and ctx.exposure and ctx.exposure.pathway_proximity:
        return 0.8, "fallen tree near verified pathway landmark"
    return 0.0, "no accessibility obstruction signal"


def school_proximity_signal(ctx: RiskContext) -> tuple[float, str]:
    """Near-school risk; children exposure raises severity urgently."""
    if not ctx.exposure or ctx.exposure.nearest_school_m is None:
        return 0.0, "no school proximity data"
    d = ctx.exposure.nearest_school_m
    if d <= 300:
        return 1.0, f"within 300 m of school ({d:.0f} m)"
    if d <= 1000:
        return 0.5, f"within 1 km of school ({d:.0f} m)"
    return 0.0, f"school beyond 1 km ({d:.0f} m)"


def hospital_proximity_signal(ctx: RiskContext) -> tuple[float, str]:
    """Emergency-response asset proximity raises priority (not severity)."""
    if not ctx.exposure or ctx.exposure.nearest_hospital_m is None:
        return 0.0, "no hospital proximity data"
    d = ctx.exposure.nearest_hospital_m
    if d <= 500:
        return 1.0, f"within 500 m of hospital ({d:.0f} m)"
    if d <= 2000:
        return 0.5, f"within 2 km of hospital ({d:.0f} m)"
    return 0.0, f"hospital beyond 2 km ({d:.0f} m)"


def traffic_signal(ctx: RiskContext) -> tuple[float, str]:
    """Traffic exposure from map reasoning (road class / junction density)."""
    if not ctx.exposure:
        return 0.0, "no traffic exposure data"
    mapping = {"high": 1.0, "moderate": 0.5, "low": 0.0}
    return mapping[ctx.exposure.traffic_exposure], (
        f"traffic exposure {ctx.exposure.traffic_exposure} "
        f"(junction density {ctx.exposure.junction_density_1km}/km2)"
    )


def repeated_report_signal(count: int) -> tuple[float, str]:
    """Repeated reports pressure: 1 - exp(-k), saturating at ~4+ reports."""
    k = max(0, count - 1)
    score = 1.0 - math.exp(-k / 2.0)
    return round(score, 4), f"{count} report(s) merged (repeated pressure {score:.2f})"


def longevity_signal(open_hours: float) -> tuple[float, str]:
    """Time-unresolved pressure, saturating after ~14 days."""
    score = math.tanh(open_hours / 336.0)  # 336 h = 14 days
    return round(score, 4), f"open {open_hours:.1f} h (longevity pressure {score:.2f})"


def weather_escalation_signal(ctx: RiskContext) -> tuple[float, str]:
    """Rain escalation for flood-prone categories (water/fallen tree)."""
    rain = ctx.rain_intensity_mm_h
    if rain is None:
        return 0.0, "no rain intensity data"
    canon = normalize_category(ctx.category)
    if canon not in ("water_leak", "fallen_tree"):
        return 0.0, "category not rain-sensitive"
    if rain >= 50:
        return 1.0, f"very heavy rain {rain:.0f} mm/h on {canon}"
    if rain >= 20:
        return 0.5, f"heavy rain {rain:.0f} mm/h on {canon}"
    return 0.0, f"rain {rain:.0f} mm/h below escalation threshold"


FEATURE_KEYS = [
    "category_base",
    "school_proximity",
    "hospital_proximity",
    "traffic",
    "electrical",
    "public_health",
    "accessibility",
    "repeated_reports",
    "longevity",
    "weather",
]


def assemble_feature_vector(ctx: RiskContext) -> tuple[dict[str, float], dict[str, str]]:
    """Full normalized feature vector plus provenance strings.

    Returns (features, provenance) where provenance[feature] explains the
    feature value in human terms.
    """
    f: dict[str, float] = {}
    p: dict[str, str] = {}
    base, base_basis = category_base_severity(ctx.category)
    f["category_base"], p["category_base"] = base, base_basis
    school, school_basis = school_proximity_signal(ctx)
    f["school_proximity"], p["school_proximity"] = school, school_basis
    hospital, hospital_basis = hospital_proximity_signal(ctx)
    f["hospital_proximity"], p["hospital_proximity"] = hospital, hospital_basis
    traffic, traffic_basis = traffic_signal(ctx)
    f["traffic"], p["traffic"] = traffic, traffic_basis
    electrical, electrical_basis = electric_risk_signal(ctx)
    f["electrical"], p["electrical"] = electrical, electrical_basis
    health, health_basis = public_health_signal(ctx)
    f["public_health"], p["public_health"] = health, health_basis
    access, access_basis = accessibility_signal(ctx)
    f["accessibility"], p["accessibility"] = access, access_basis
    repeat, repeat_basis = repeated_report_signal(ctx.repeated_reports)
    f["repeated_reports"], p["repeated_reports"] = repeat, repeat_basis
    longevity, longevity_basis = longevity_signal(ctx.open_hours)
    f["longevity"], p["longevity"] = longevity, longevity_basis
    weather, weather_basis = weather_escalation_signal(ctx)
    f["weather"], p["weather"] = weather, weather_basis
    return f, p


def description_token_exposure(description: str) -> list[str]:
    """Tokenized description for traceability (no named-entity guessing)."""
    return re.findall(r"[a-z0-9]{3,}", description.lower())