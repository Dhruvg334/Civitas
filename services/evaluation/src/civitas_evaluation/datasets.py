"""Frozen labelled test sets for every Member 2 capability (Phase 11/12).

Split discipline (the invariant of this phase):

- The vision classifier trains on the synthetic corpus baked into
  `civitas_vision.benchmark` (seeds 1..N per class). Development-phase
  benchmark evaluations used held-out seeds >= 1000. The FINAL test set
  below uses seeds 2000-2049 - disjoint from both - generated ONCE,
  written to `test_data/`, sha256-pinned in a manifest and committed.
  Later runs read the identical pixels; nothing in this package retrains
  or re-tunes (duplicate_threshold=0.70, band thresholds, quality gates
  all stay at their production defaults).
- The test set is NEVER regenerated after results have been produced:
  `regenerate-testset` refuses to run when `results/` already exists.
- All examples are synthetic (procedural generators or hand-authored
  evidence records) and are explicitly labelled as such - they are never
  presented as real-world evidence. This is a recorded limitation.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from civitas_risk import priority_features as _prio_feat

# Documented rule/weight mirrors used ONLY to author the risk labels. The
# evaluation package must not silently copy the models' internals, so these
# constants are guarded: if the documented tables ever drift from what the
# models ship, the drift-asserts below fail loudly and the labels must be
# re-derived consciously (circularity is disclosed in risk_eval.py notes).
from civitas_risk import severity_model as _sev
from civitas_risk.priority_model import PriorityModel as _PriorityModel
from civitas_vision.benchmark import SIZE, gaussian_blur, make_image
from PIL import Image

assert _sev.RULE_POINTS == {
    "active_water_flow": 12,
    "significant_coverage": 8,
    "slip_hazard": 5,
    "school_near": 10,
    "school_zone": 5,
    "hospital_near": 4,
    "traffic_high": 7,
    "traffic_moderate": 5,
    "crowd_per_extra_report": 4,
    "duration_per_hour": 2,
    "rain_heavy": 5,
}, "severity rule table drifted from the documented values"
assert _sev.CATEGORY_BASE_POINTS == {
    "pothole": 55,
    "water_leak": 50,
    "garbage": 45,
    "streetlight": 35,
    "fallen_tree": 65,
}, "category base table drifted from the documented values"
assert abs(_sev._SEVERITY_SQUASH_SCALE - 66.0) < 1e-9
assert _PriorityModel.WEIGHTS == {
    "severity_score": 0.25,
    "school_proximity": 0.18,
    "hospital_proximity": 0.08,
    "traffic_exposure": 0.12,
    "population_exposure": 0.07,
    "repeated_reports": 0.10,
    "incident_duration": 0.05,
    "nearby_density": 0.05,
    "category_urgency": 0.05,
    "time_sensitivity": 0.05,
}, "priority weight table drifted from the documented values"
assert _prio_feat.CATEGORY_URGENCY == {
    "pothole": 0.4,
    "water_leak": 0.6,
    "garbage": 0.8,
    "streetlight": 0.2,
    "fallen_tree": 0.5,
}, "category urgency table drifted from the documented values"
assert _prio_feat.UNKNOWN_CATEGORY_URGENCY == 0.4
assert _prio_feat._SCHOOL_NEAR_M == 300
assert _prio_feat._SCHOOL_ZONE_M == 1000
assert _prio_feat._HOSPITAL_NEAR_M == 500
assert _prio_feat._HOSPITAL_ZONE_M == 2000
assert _prio_feat._RAIN_HEAVY_MM_H == 20.0
# Engineering mappings from priority_features.
assert abs(_prio_feat.time_sensitivity_signal(_dt.datetime(2026, 3, 2, 10))[0] - 0.8) < 1e-9
assert abs(
    _prio_feat.time_sensitivity_signal(_dt.datetime(2026, 3, 2, 10), 25)[0] - 1.0
) < 1e-9
assert abs(
    _prio_feat.time_sensitivity_signal(_dt.datetime(2026, 3, 2, 23))[0] - 0.2
) < 1e-9

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[3]
TEST_DATA_DIR = REPO_ROOT / "services" / "evaluation" / "test_data"
RESULTS_DIR = REPO_ROOT / "services" / "evaluation" / "results"

# Vision: 5 Civitas MVP categories x 10 images = 50 untouched examples.
VISION_CATEGORIES = [
    "pothole_road_damage",
    "water_leakage",
    "garbage_overflow",
    "broken_streetlight",
    "fallen_tree",
]
VISION_TEST_SEEDS: dict[str, list[int]] = {
    cat: list(range(2000 + i * 10, 2000 + i * 10 + 10)) for i, cat in enumerate(VISION_CATEGORIES)
}

EQUATOR = 28.6139
MERIDIAN = 77.2090


def _utc(y: int, m: int, d: int, h: int = 8) -> str:
    return _dt.datetime(y, m, d, h, 0, tzinfo=_dt.timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Labelled definitions (frozen by construction: deterministic seeds +
# constants below; the generated artifacts are committed and never edited)
# ---------------------------------------------------------------------------

MEDIA_QUALITY_CASES = [
    # (case_id, kind, expected_usable, category, seed, variant, note)
    ("mq-valid-water", "valid", True, "water_leakage", 2050, "flow", "valid flowing-water scene"),
    ("mq-valid-pothole", "valid", True, "pothole_road_damage", 2051, "default", "valid pothole scene"),
    ("mq-valid-garbage", "valid", True, "garbage_overflow", 2052, "default", "valid garbage scene"),
    ("mq-blur-water", "blurred", False, "water_leakage", 2060, "default", "radius-4 gaussian blur"),
    ("mq-blur-pothole", "blurred", False, "pothole_road_damage", 2061, "default", "radius-4 gaussian blur"),
    ("mq-blur-streetlight", "blurred", False, "broken_streetlight", 2062, "default", "radius-4 gaussian blur"),
    ("mq-tiny", "tiny", False, "pothole_road_damage", 2063, "default", "32x32 px, below 64px minimum"),
    ("mq-dark", "near-black", False, "fallen_tree", 2064, "default", "flat luminance ~0.01"),
    ("mq-bright", "over-exposed", False, "garbage_overflow", 2065, "default", "flat luminance ~0.99"),
    ("mq-ambiguous-blend", "ambiguous", True, None, None, None, "50/50 pixel blend of two committed training-prototype scenes (water flow + pothole); derived input, not itself a training example; must flag low confidence instead of asserting"),
    ("mq-unsupported-bytes", "unsupported", False, None, None, None, "bytes that are not a decodable image"),
    ("mq-missing-file", "missing", False, None, None, None, "local_path does not exist"),
    ("mq-video-no-path", "video-no-path", False, None, None, None, "kind=video with no local path (backend video bytes unsupported)"),
    ("mq-no-media", "no-media", False, None, None, None, "no media attached to the report"),
]


def _ambiguous_blend() -> Image.Image:
    water = np.asarray(make_image("water_leakage", 7101, "flow")).astype(np.float64)
    pothole = np.asarray(make_image("pothole_road_damage", 7300)).astype(np.float64)
    return Image.fromarray((water * 0.5 + pothole * 0.5).astype(np.uint8))


def _report(
    report_id: str,
    description: str,
    lat: float,
    lng: float,
    at: str,
    category: str,
) -> dict[str, object]:
    return {
        "report_id": report_id,
        "description": description,
        "latitude": lat,
        "longitude": lng,
        "submitted_at": at,
        "category": category,
    }


# Pairs: 6 positive (same physical incident), 5 clearly negative,
# 4 hard negatives (1 nearby-but-unrelated, 1 similar-text,
# 1 same-location-different-category, 1 different-time).
DUPLICATE_PAIRS: list[dict[str, object]] = []

for i in range(6):
    base = 28.6100 + i * 0.003
    desc_a = "water leaking from the pipe near the school gate, water across the road"
    desc_b = "water pipeline leak at the school gate, road wet and flowing"
    DUPLICATE_PAIRS.append(
        {
            "pair_id": f"dup-pos-{i}",
            "kind": "positive",
            "label": 1,
            "hard": False,
            "reports": (
                _report(f"POS-{i}-A", desc_a, base, MERIDIAN, _utc(2026, 3, 1, 8), "water_leakage"),
                _report(f"POS-{i}-B", desc_b, base + 0.0004, MERIDIAN, _utc(2026, 3, 1, 13), "water_leakage"),
            ),
        }
    )

for i in range(5):
    DUPLICATE_PAIRS.append(
        {
            "pair_id": f"dup-neg-{i}",
            "kind": "negative",
            "label": 0,
            "hard": False,
            "reports": (
                _report(f"NEG-{i}-A", "broken streetlight on the main road", 28.6000 + i * 0.01, MERIDIAN, _utc(2026, 3, 1, 8), "broken_streetlight"),
                _report(f"NEG-{i}-B", "garbage pile overflowing near the market", 28.6800 + i * 0.01, MERIDIAN, _utc(2026, 3, 1, 9), "garbage_overflow"),
            ),
        }
    )

hard_nearby = [
    ("H1-A", "water leaking at the corner shop, footpath wet", 28.6200, "water_leakage"),
    ("H1-B", "pothole at the corner shop, front wheel damaged", 28.6203, "pothole_road_damage"),
]
hard_similar_text = [
    ("H2-A", "pothole near the metro pillar, repair needed badly", 28.6301, "pothole_road_damage"),
    ("H2-B", "pothole near the metro pillar, repair needed badly", 28.6420, "pothole_road_damage"),
]
hard_same_loc = [
    ("H3-A", "fallen tree blocking the footpath exit", 28.6150, "fallen_tree"),
    ("H3-B", "garbage overflow pile at the footpath exit", 28.6152, "garbage_overflow"),
]
hard_diff_time = [
    ("H4-A", "water leak on station road, flowing across", 28.6250, "water_leakage"),
    ("H4-B", "water leak on station road, flowing across", 28.6251, "water_leakage"),
]

_hard_groups: list[tuple[str, list[tuple[str, str, float, str]], list[tuple[str, str, float, str]], bool]] = [
    ("nearby-unrelated", hard_nearby, hard_nearby, False),
    ("similar-text-different-location", hard_similar_text, hard_similar_text, False),
    ("same-location-different-category", hard_same_loc, hard_same_loc, False),
    ("different-time", hard_diff_time, hard_diff_time, True),
]

for kind, group_a, group_b, different_time in _hard_groups:
    (ida, da, la, ca), (idb, db, lb, cb) = group_a[0], group_b[1]
    DUPLICATE_PAIRS.append(
        {
            "pair_id": f"dup-hard-{kind}",
            "kind": kind,
            "label": 0,
            "hard": True,
            "reports": (
                _report(ida, da, la, MERIDIAN, _utc(2026, 3, 1, 8), ca),
                _report(
                    idb, db, lb, MERIDIAN,
                    _utc(2026, 3, 5, 8) if different_time else _utc(2026, 3, 1, 9),
                    cb,
                ),
            ),
        }
    )


# Cluster scenarios: expected consolidation (report_ids per expected cluster).
CLUSTER_SCENARIOS: list[dict[str, object]] = [
    {
        "scenario_id": "cl-same-incident",
        "expected_clusters": [{"incident": "first", "report_ids": ["CA-1", "CA-2", "CA-3"]}],
        "reports": [
            _report("CA-1", "water leak at the school gate, flooding the footpath", 28.6100 + 0.001, MERIDIAN, _utc(2026, 3, 1, 8), "water_leakage"),
            _report("CA-2", "water pipeline leak near school, road flooded", 28.6103, MERIDIAN, _utc(2026, 3, 1, 10), "water_leakage"),
            _report("CA-3", "leaking pipe at school gate area, water everywhere", 28.6105, MERIDIAN, _utc(2026, 3, 1, 12), "water_leakage"),
        ],
    },
    {
        "scenario_id": "cl-nearby-incidents",
        "expected_clusters": [
            {"incident": "A", "report_ids": ["CB-1", "CB-2"]},
            {"incident": "B", "report_ids": ["CB-3", "CB-4"]},
        ],
        "reports": [
            _report("CB-1", "water leak near the bank building entrance", 28.6300, MERIDIAN, _utc(2026, 3, 2, 8), "water_leakage"),
            _report("CB-2", "pipe burst at the bank building, water on road", 28.6302, MERIDIAN, _utc(2026, 3, 2, 11), "water_leakage"),
            _report("CB-3", "pothole near the hospital side gate", 28.6400, MERIDIAN, _utc(2026, 3, 2, 8), "pothole_road_damage"),
            _report("CB-4", "deep pothole outside the hospital gate", 28.6402, MERIDIAN, _utc(2026, 3, 2, 13), "pothole_road_damage"),
        ],
    },
    {
        "scenario_id": "cl-confusable-pair",
        "expected_clusters": [
            {"incident": "X", "report_ids": ["CC-1", "CC-2"]},
            {"incident": "Y", "report_ids": ["CC-3", "CC-4"]},
        ],
        "reports": [
            _report("CC-1", "pothole near the metro pillar, repair needed badly", 28.6301, MERIDIAN, _utc(2026, 3, 3, 8), "pothole_road_damage"),
            _report("CC-2", "pothole near the metro pillar, repair needed badly", 28.6303, MERIDIAN, _utc(2026, 3, 3, 9), "pothole_road_damage"),
            _report("CC-3", "pothole near the metro pillar, repair needed badly", 28.6420, MERIDIAN, _utc(2026, 3, 3, 8), "pothole_road_damage"),
            _report("CC-4", "pothole near the metro pillar, repair needed badly", 28.6422, MERIDIAN, _utc(2026, 3, 3, 10), "pothole_road_damage"),
        ],
    },
    {
        "scenario_id": "cl-same-location-different-category",
        "expected_clusters": [
            {"incident": "P", "report_ids": ["CD-1", "CD-2"]},
            {"incident": "Q", "report_ids": ["CD-3", "CD-4"]},
        ],
        "reports": [
            _report("CD-1", "fallen tree blocking the footpath exit", 28.6150, MERIDIAN, _utc(2026, 3, 4, 8), "fallen_tree"),
            _report("CD-2", "tree fell across the footpath exit", 28.6152, MERIDIAN, _utc(2026, 3, 4, 14), "fallen_tree"),
            _report("CD-3", "garbage overflow pile at the footpath exit", 28.6154, MERIDIAN, _utc(2026, 3, 4, 8), "garbage_overflow"),
            _report("CD-4", "waste overflowing near the footpath exit", 28.6156, MERIDIAN, _utc(2026, 3, 4, 12), "garbage_overflow"),
        ],
    },
]


# ---------------------------------------------------------------------------
# Severity / priority label authoring from the DOCUMENTED rule and weight
# tables (guarded against drift above). The same arithmetic the models
# implement, re-expressed here as ground truth labels.
# ---------------------------------------------------------------------------

def _severity_expected(facts: dict[str, Any]) -> tuple[int, str]:
    """(score, level) for incident facts, per the documented severity table."""
    cat = str(facts["category"])
    points = float(_sev.CATEGORY_BASE_POINTS.get(cat, _sev.UNKNOWN_CATEGORY_POINTS))
    flow = int(facts.get("active_water_flow", 0)) == 1
    traffic = facts.get("traffic_exposure")
    if flow:
        points += _sev.RULE_POINTS["active_water_flow"]
    if float(facts.get("water_coverage", 0.0)) >= 0.30:
        points += _sev.RULE_POINTS["significant_coverage"]
    if flow and traffic in ("high", "moderate"):
        points += _sev.RULE_POINTS["slip_hazard"]
    school = facts.get("school_distance_m")
    if school is not None and float(school) <= _sev._SCHOOL_NEAR_M:
        points += _sev.RULE_POINTS["school_near"]
    elif school is not None and float(school) <= _sev._SCHOOL_ZONE_M:
        points += _sev.RULE_POINTS["school_zone"]
    hospital = facts.get("hospital_distance_m")
    if hospital is not None and float(hospital) <= _sev._HOSPITAL_NEAR_M:
        points += _sev.RULE_POINTS["hospital_near"]
    if traffic == "high":
        points += _sev.RULE_POINTS["traffic_high"]
    elif traffic == "moderate":
        points += _sev.RULE_POINTS["traffic_moderate"]
    crowd = min(
        9,
        _sev.RULE_POINTS["crowd_per_extra_report"]
        * max(0, int(facts.get("report_count", 1)) - 1),
    )
    points += crowd
    duration_pts = min(
        8, _sev.RULE_POINTS["duration_per_hour"] * round(float(facts.get("duration_hours", 0)))
    )
    points += duration_pts
    rain = facts.get("rain_intensity_mm_h")
    if rain is not None and float(rain) >= 20.0:
        points += _sev.RULE_POINTS["rain_heavy"]
    score = int(round(100.0 * (1.0 - math.exp(-points / _sev._SEVERITY_SQUASH_SCALE))))
    if score >= 80:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"
    return score, level


def _priority_engineering(facts: dict[str, Any], ctx: dict[str, Any]) -> dict[str, float]:
    """Expected engineered signal values, per the documented mappings."""
    severity_score, _ = _severity_expected(facts)
    school_m = facts.get("school_distance_m")
    if school_m is not None and float(school_m) <= _prio_feat._SCHOOL_NEAR_M:
        school = 1.0
    elif school_m is not None and float(school_m) <= _prio_feat._SCHOOL_ZONE_M:
        school = 0.5
    else:
        school = 0.0
    hospital_m = facts.get("hospital_distance_m")
    if hospital_m is not None and float(hospital_m) <= _prio_feat._HOSPITAL_NEAR_M:
        hospital = 1.0
    elif hospital_m is not None and float(hospital_m) <= _prio_feat._HOSPITAL_ZONE_M:
        hospital = 0.5
    else:
        hospital = 0.0
    traffic = {"high": 1.0, "moderate": 0.5}.get(str(facts.get("traffic_exposure")), 0.0)
    population = ctx.get("population_density_proxy")
    population_sig = max(0.0, min(1.0, float(population))) if population is not None else 0.0
    reports_sig = 1.0 - math.exp(-max(0, int(facts.get("report_count", 1)) - 1) / 2.0)
    duration_sig = math.tanh(float(facts.get("duration_hours", 0.0)) / 24.0)
    density = ctx.get("nearby_density_norm")
    density_sig = max(0.0, min(1.0, float(density))) if density is not None else 0.0
    urgency_sig = _prio_feat.CATEGORY_URGENCY.get(
        _prio_feat.CATEGORY_ALIASES.get(str(facts["category"]).strip().lower(), str(facts["category"]).strip().lower()),
        _prio_feat.UNKNOWN_CATEGORY_URGENCY,
    )
    current_time = ctx.get("current_time")
    time_sig = 0.5
    if current_time is not None:
        hour = _dt.datetime.fromisoformat(str(current_time)).time()
        if _dt.time(7, 0) <= hour <= _dt.time(19, 0):
            time_sig = 0.8
        elif _dt.time(19, 0) < hour <= _dt.time(22, 0):
            time_sig = 0.4
        else:
            time_sig = 0.2
    rain = facts.get("rain_intensity_mm_h")
    if rain is not None and float(rain) >= _prio_feat._RAIN_HEAVY_MM_H:
        time_sig = min(1.0, time_sig + 0.2)
    return {
        "severity_score": round(severity_score / 100.0, 4),
        "school_proximity": round(school, 4),
        "hospital_proximity": round(hospital, 4),
        "traffic_exposure": round(traffic, 4),
        "population_exposure": round(population_sig, 4),
        "repeated_reports": round(reports_sig, 4),
        "incident_duration": round(duration_sig, 4),
        "nearby_density": round(density_sig, 4),
        "category_urgency": round(urgency_sig, 4),
        "time_sensitivity": round(time_sig, 4),
    }


_PRIORITY_BANDS = (("critical", 80), ("high", 60), ("medium", 40), ("low", 0))


def _priority_expected(
    facts: dict[str, object], ctx: dict[str, object]
) -> tuple[str, int, dict[str, float], list[str]]:
    """(level, score, signal values, reason keys) for priority facts."""
    signals = _priority_engineering(facts, ctx)
    score = round(
        100.0 * sum(_PriorityModel.WEIGHTS[k] * signals[k] for k in _PriorityModel.WEIGHTS)
    )
    score = max(0, min(100, score))
    level = "critical" if score >= 80 else "high" if score >= 60 else "medium" if score >= 40 else "low"
    reasons = [
        k for k in _PriorityModel.WEIGHTS if round(100.0 * _PriorityModel.WEIGHTS[k] * signals[k]) >= 1
    ]
    return level, score, signals, reasons


def severity_label_bands() -> list[dict[str, object]]:
    """12 hand-authored severity cases; expected levels are COMPUTED by
    `_severity_expected` from the documented rule table (same published
    constants the model implements, disclosed as circular in risk_eval)."""
    cases = [
        {"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.5,
         "school_distance_m": 120, "hospital_distance_m": None, "traffic_exposure": "high",
         "report_count": 4, "duration_hours": 20, "rain_intensity_mm_h": 30},
        {"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.4,
         "school_distance_m": 450, "hospital_distance_m": None, "traffic_exposure": "moderate",
         "report_count": 2, "duration_hours": 6, "rain_intensity_mm_h": None},
        {"category": "fallen_tree", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "high",
         "report_count": 3, "duration_hours": 30, "rain_intensity_mm_h": None},
        {"category": "garbage", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": 700, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 3, "rain_intensity_mm_h": None},
        {"category": "pothole", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "streetlight", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "fallen_tree", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": 80, "hospital_distance_m": 300, "traffic_exposure": "high",
         "report_count": 5, "duration_hours": 40, "rain_intensity_mm_h": 25},
        {"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.05,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "high",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "water_leak", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "streetlight", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "moderate",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "garbage", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
        {"category": "pothole", "active_water_flow": 0, "water_coverage": 0.0,
         "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
         "report_count": 1, "duration_hours": 2, "rain_intensity_mm_h": None},
    ]
    rows = []
    for i, feats in enumerate(cases):
        score, level = _severity_expected(feats)
        rows.append(
            {
                "case_id": f"sev-{i:02d}",
                "expected_level": level,
                "expected_score": score,
                "features": feats,
            }
        )
    return rows


def priority_label_cases() -> list[dict[str, object]]:
    """12 hand-authored priority cases. Facts + context are authored; the
    expected level, expected severity score, expected engineered signal
    values and expected reason keys are COMPUTED here from the documented
    10-signal semantics (weights, proximity thresholds, urgency table),
    guarded against drift at the top of this module."""
    cases = [
        # (incident facts, context) — see design: 3 critical, 3 high,
        # 3 medium, 3 low; pairs ("water_leak" flow .. ) diverge on purpose.
        ({"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.5,
          "school_distance_m": 120, "hospital_distance_m": 300, "traffic_exposure": "high",
          "report_count": 4, "duration_hours": 20, "rain_intensity_mm_h": 30},
         {"population_density_proxy": 0.85, "nearby_density_norm": 0.5, "current_time": "2026-03-02T08:00:00+00:00"}),
        ({"category": "fallen_tree", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 80, "hospital_distance_m": 300, "traffic_exposure": "high",
          "report_count": 5, "duration_hours": 40, "rain_intensity_mm_h": 25},
         {"population_density_proxy": 0.8, "nearby_density_norm": 0.6, "current_time": "2026-03-02T10:00:00+00:00"}),
        ({"category": "garbage", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 150, "hospital_distance_m": 200, "traffic_exposure": "high",
          "report_count": 5, "duration_hours": 30, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.9, "nearby_density_norm": 0.7, "current_time": "2026-03-02T12:00:00+00:00"}),
        ({"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.4,
          "school_distance_m": 450, "hospital_distance_m": None, "traffic_exposure": "high",
          "report_count": 3, "duration_hours": 8, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.5, "nearby_density_norm": 0.3, "current_time": "2026-03-02T10:00:00+00:00"}),
        ({"category": "garbage", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 900, "hospital_distance_m": 1600, "traffic_exposure": "moderate",
          "report_count": 3, "duration_hours": 12, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.9, "nearby_density_norm": 0.4, "current_time": "2026-03-02T09:00:00+00:00"}),
        ({"category": "pothole", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 900, "hospital_distance_m": 1800, "traffic_exposure": "high",
          "report_count": 3, "duration_hours": 12, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.6, "nearby_density_norm": 0.5, "current_time": "2026-03-02T17:00:00+00:00"}),
        ({"category": "streetlight", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
          "report_count": 1, "duration_hours": 1, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.2, "nearby_density_norm": 0.1, "current_time": "2026-03-02T02:00:00+00:00"}),
        ({"category": "pothole", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
          "report_count": 1, "duration_hours": 2, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.1, "nearby_density_norm": 0.1, "current_time": "2026-03-02T23:00:00+00:00"}),
        ({"category": "water_leak", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 200, "hospital_distance_m": None, "traffic_exposure": "moderate",
          "report_count": 1, "duration_hours": 2, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.4, "nearby_density_norm": 0.3, "current_time": "2026-03-02T21:00:00+00:00"}),
        ({"category": "water_leak", "active_water_flow": 1, "water_coverage": 0.0,
          "school_distance_m": 700, "hospital_distance_m": None, "traffic_exposure": "moderate",
          "report_count": 3, "duration_hours": 6, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.5, "nearby_density_norm": 0.2, "current_time": "2026-03-02T15:00:00+00:00"}),
        ({"category": "garbage", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": 600, "hospital_distance_m": 1500, "traffic_exposure": "moderate",
          "report_count": 2, "duration_hours": 8, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.6, "nearby_density_norm": 0.5, "current_time": "2026-03-02T08:00:00+00:00"}),
        ({"category": "streetlight", "active_water_flow": 0, "water_coverage": 0.0,
          "school_distance_m": None, "hospital_distance_m": None, "traffic_exposure": "low",
          "report_count": 1, "duration_hours": 3, "rain_intensity_mm_h": None},
         {"population_density_proxy": 0.1, "nearby_density_norm": 0.1, "current_time": "2026-03-02T03:00:00+00:00"}),
    ]
    rows = []
    for i, (facts, ctx) in enumerate(cases):
        level, score, signals, reasons = _priority_expected(facts, ctx)
        rows.append(
            {
                "case_id": f"pri-{i:02d}",
                "expected_level": level,
                "expected_score": score,
                "expected_severity_score": _severity_expected(facts)[0],
                "expected_signals": signals,
                "expected_reasons": reasons,
                "incident": facts,
                "context": ctx,
            }
        )
    return rows


def resolution_cases() -> list[dict[str, object]]:
    """16 hand-authored before/after cases across the four outcomes."""
    def ev(stage: str, evidence: list[str], coverage: float, usable: bool = True) -> dict[str, object]:
        return {"stage": stage, "observable_evidence": evidence, "water_coverage": coverage, "media_usable": usable}

    cases = [
        ("resolved", ev("before", ["water flowing across road"], 0.5), ev("after", ["repaired road"], 0.02)),
        ("resolved", ev("before", ["water flowing across road", "standing water"], 0.6), ev("after", [], 0.01)),
        ("resolved", ev("before", ["water flowing across road"], 0.35), ev("after", ["dry asphalt"], 0.0)),
        ("resolved", ev("before", ["water flowing across road"], 0.45), ev("after", [], 0.04)),
        ("partial", ev("before", ["water flowing across road"], 0.5), ev("after", ["standing water"], 0.3)),
        ("partial", ev("before", ["water flowing across road"], 0.7), ev("after", ["standing water"], 0.22)),
        ("partial", ev("before", ["water flowing across road", "standing water"], 0.8), ev("after", ["standing water", "wet road"], 0.35)),
        ("partial", ev("before", ["water flowing across road"], 0.55), ev("after", ["standing water"], 0.25)),
        ("unverifiable", ev("before", [], 0.0), ev("after", [], 0.0)),
        ("unverifiable", ev("before", ["standing water"], 0.2, usable=False), ev("after", [], 0.0)),
        ("unverifiable", ev("before", [], 0.0), ev("after", [], 0.0, usable=False)),
        ("unverifiable", ev("before", ["dark scene"], 0.0, usable=False), ev("after", ["dark scene"], 0.0, usable=False)),
        ("conflicting", ev("before", ["water flowing across road"], 0.3), ev("after", ["water flowing across road"], 0.6)),
        ("conflicting", ev("before", [], 0.0), ev("after", ["water flowing across road"], 0.5)),
        ("conflicting", ev("before", ["water flowing across road"], 0.4), ev("after", ["standing water"], 0.55)),
        ("conflicting", ev("before", ["water flowing across road"], 0.25), ev("after", ["fallen trunk across road"], 0.0)),
    ]
    return [
        {"case_id": f"res-{i:02d}", "expected_outcome": outcome, "before": before, "after": after}
        for i, (outcome, before, after) in enumerate(cases)
    ]


# ---------------------------------------------------------------------------
# Generation + manifest (run once; artifacts committed; see module docstring)
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _write_labeled(relative: str, labels: list[dict[str, object]]) -> Path:
    path = TEST_DATA_DIR / relative
    _write_json(path, labels)
    return path


def generate_test_set() -> dict[str, object]:
    """Bootstrap only: ORIGINAL unconditional generation writes the frozen
    artifacts; refused once results exist so the untouched test set cannot
    be silently replaced after looking at metrics."""
    if any(RESULTS_DIR.glob("*.json")) or list(RESULTS_DIR.glob("*/")):
        raise RuntimeError(
            "refusing to regenerate the test set: results already exist. "
            "The untouched test set is frozen; delete results/ only to"
            " re-run evaluations against the SAME test set."
        )

    # Vision images + labels
    vision_labels: list[dict[str, object]] = []
    for category, seeds in VISION_TEST_SEEDS.items():
        out_dir = TEST_DATA_DIR / "vision" / "images" / category
        out_dir.mkdir(parents=True, exist_ok=True)
        for seed in seeds:
            case_id = f"vis-{category}-{seed}"
            image = make_image(category, seed)
            image.save(out_dir / f"{case_id}.png")
            vision_labels.append(
                {"case_id": case_id, "category": category, "seed": seed, "expected": category}
            )
    vision_labels_path = _write_labeled("vision/labels.json", vision_labels)

    # Media-quality labels + artifacts
    media_labels: list[dict[str, object]] = []
    media_dir = TEST_DATA_DIR / "media_quality"
    media_dir.mkdir(parents=True, exist_ok=True)
    for case in MEDIA_QUALITY_CASES:
        case_id, kind, expected_usable, case_category, case_seed, variant, note = case
        media_labels.append(
            {
                "case_id": case_id,
                "kind": kind,
                "expected_usable": expected_usable,
                "category": case_category,
                "note": note,
            }
        )
        if kind == "valid" or kind == "blurred" or kind == "tiny":
            img = make_image(case_category, case_seed)
            if kind == "blurred":
                img = gaussian_blur(img)
            if kind == "tiny":
                img = img.resize((32, 32), Image.Resampling.BILINEAR)
            img.save(media_dir / f"{case_id}.png")
        elif kind == "near-black":
            Image.fromarray(np.full((SIZE, SIZE, 3), 3, dtype=np.uint8)).save(media_dir / f"{case_id}.png")
        elif kind == "over-exposed":
            Image.fromarray(np.full((SIZE, SIZE, 3), 252, dtype=np.uint8)).save(media_dir / f"{case_id}.png")
        elif kind == "ambiguous":
            _ambiguous_blend().save(media_dir / f"{case_id}.png")
        elif kind == "unsupported":
            (media_dir / f"{case_id}.bin").write_bytes(b"this is not an image - just text bytes")
    media_labels_path = _write_labeled("media_quality/labels.json", media_labels)

    fixed: list[tuple[str, list[dict[str, object]]]] = [
        ("duplicates/labels.json", [dict(p) for p in DUPLICATE_PAIRS]),
        ("clusters/labels.json", [dict(s) for s in CLUSTER_SCENARIOS]),
        ("severity/labels.json", severity_label_bands()),
        ("priority/labels.json", priority_label_cases()),
        ("resolution/labels.json", resolution_cases()),
    ]
    paths = {name: path for name, path in [("vision", vision_labels_path), ("media_quality", media_labels_path)]}
    for relative, labels in fixed:
        paths[relative.split("/")[0]] = _write_labeled(relative, labels)

    files = sorted(
        path
        for path in TEST_DATA_DIR.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest: dict[str, object] = {
        "policy": (
            "frozen once, never regenerated after results exist; synthetic "
            "procedural imagery (civitas_vision.benchmark) and hand-authored "
            "evidence records; NO real-world or citizen imagery is used or claimed"
        ),
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "vision_test_seed_ranges": {
            cat: [min(s), max(s)] for cat, s in VISION_TEST_SEEDS.items()
        },
        "vision_train_origin": "civitas_vision.benchmark corpus (seeds 1..N), disjoint from test seeds",
        "ambiguous_blend_provenance": (
            "50/50 pixel blend of committed training-prototype scenes "
            "(water flow 7101 + pothole 7300); derived input testing the "
            "ambiguity gate, not itself a training example; disclosed as derived"
        ),
        "files": {str(path.relative_to(TEST_DATA_DIR)): _sha256(path) for path in files},
    }
    _write_json(TEST_DATA_DIR / "manifest.json", manifest)
    return manifest


def load_labels(relative: str) -> list[dict[str, object]]:
    path = TEST_DATA_DIR / relative
    if not path.exists():
        raise FileNotFoundError(
            f"frozen test set missing: {path}. Run 'python -m civitas_evaluation "
            f"regenerate-testset' once to bootstrap it (refused after results exist)."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def vision_image(case_id: str) -> Image.Image:
    path = next(TEST_DATA_DIR.glob(f"vision/images/*/{case_id}.png"))
    return Image.open(path)


def media_image(case_id: str) -> Image.Image:
    return Image.open(TEST_DATA_DIR / "media_quality" / f"{case_id}.png")


def media_file(case_id: str) -> Path:
    return TEST_DATA_DIR / "media_quality" / f"{case_id}.bin"