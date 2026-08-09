"""Observable-evidence extraction from measurements (Phase 3).

The `observable_evidence` list in the product contract is derived from real
pixel measurements (`civitas_vision.features`), never from a language model.
Thresholds below were calibrated on the synthetic benchmark's in/out
distributions (see `benchmark.py`); each rule records the measurements that
fired. Evidence is emitted only for categories with meaningful probability
(primary or >= 0.25) so the evidence list always supports the verdict.
"""

from __future__ import annotations

from PIL import Image

from civitas_vision.features import extract_features

# (category, observation, condition, basis name). Thresholds: in/out
# separation measured on the synthetic corpus, margin applied.
EVIDENCE_RULES = (
    ("water_leakage", "standing water",
     lambda f: f["blue_smooth_share"] >= 0.20,
     "blue-dominant smooth-region share >= 0.20"),
    ("water_leakage", "water flowing across road",
     lambda f: f["blue_smooth_share"] >= 0.20 and f["flow_blue_ratio"] >= 0.06,
     "blue region with horizontal ripple banding >= 0.06"),
    ("pothole_road_damage", "visible road cavity (pothole) with broken surface",
     lambda f: f["dark_lowtexture_share"] >= 0.025 and f["band_dark_ratio"] >= 0.030
     and f["edge_density"] >= 0.13,
     "dark low-texture share >= 0.025, dark banding >= 0.030, edge density >= 0.13"),
    ("garbage_overflow", "mixed-color waste pile (scattered debris)",
     lambda f: f["color_scatter"] >= 90.0 and f["saturation_mean"] >= 0.17
     and f["blue_smooth_share"] <= 0.05 and f["green_dominance"] <= 0.012,
     "color scatter >= 90, saturation >= 0.17, no standing water, no canopy green (<= 0.012)"),
    ("broken_streetlight", "dark scene with a localized bright bulb region",
     lambda f: f["bright_upper_share"] >= 0.80 and f["luminance_mean"] <= 0.35
     and f["dark_lowtexture_share"] >= 0.30,
     "bright peak in upper half >= 0.80, dark frame, large dark low-texture share"),
    ("fallen_tree", "fallen trunk/blockage spanning the road",
     lambda f: f["green_dominance"] > 0.016 and f["band_dark_ratio"] >= 0.012,
     "pronounced canopy green (> 0.016) with dark recumbent banding >= 0.012"),
)


def extract_evidence(features: dict[str, float]) -> list[str]:
    """Measurements that fired -> evidence strings (ordered by rule order)."""
    return [observation for _, observation, cond, _ in EVIDENCE_RULES if cond(features)]


def evidence_basis(features: dict[str, float]) -> list[str]:
    """Basis entries for the evidence that actually fired."""
    out: list[str] = []
    for category, observation, cond, basis_name in EVIDENCE_RULES:
        if cond(features):
            out.append(f"{category}: {observation} ({basis_name})")
    return out


def filter_evidence_for_categories(
    evidence: list[str], categories: set[str]
) -> list[str]:
    """Keep only evidence whose rule category is among the passed categories."""
    rule_by_observation = {observation: category for category, observation, _, _ in EVIDENCE_RULES}
    return [obs for obs in evidence if rule_by_observation.get(obs) in categories]


def evidence_for_image(image: Image.Image) -> tuple[list[str], dict[str, float], list[str]]:
    """Convenience: features + evidence strings + evidence basis for one image."""
    features = extract_features(image)
    return extract_evidence(features), features, evidence_basis(features)


__all__ = [
    "EVIDENCE_RULES",
    "evidence_basis",
    "evidence_for_image",
    "extract_evidence",
    "filter_evidence_for_categories",
]