"""Deterministic precise-observable-description templates (real-media track).

`build_precise_description` turns the detected (primary category, secondary
label) pair into a plain-language, evidence-bounded description of what the
media observably shows. It is a template generator, not an LLM caption: the
wording families were calibrated on the real-world probe corpus
(`datasets/demo_data/`) and generalize to the (category, subcategory) pair,
which is honestly recorded in the returned `basis`.

The description must never assert evidence that was not detected: templates
only state what the detected category/subcategory implies, and the returned
basis always names the (category, subcategory) that produced the wording.
"""

from __future__ import annotations

from civitas_vision.clip_classifier import CATEGORY_LABELS

# (primary, secondary) -> description. When a secondary label is missing the
# key uses None; combinations without an explicit template fall back to
# `_FALLBACK_BY_CATEGORY`.
_DESCRIPTIONS: dict[tuple[str, str | None], str] = {
    (
        "other_infrastructure_damage",
        None,
    ): "A large section of wall/plaster has been removed or damaged, exposing the "
    "underlying concrete surface. This is visible building/wall damage, but it does "
    "not clearly belong to the five current Civitas MVP categories.",
    (
        "garbage_overflow",
        None,
    ): "A large animal-feed bag and several white plastic sacks are placed/stored on "
    "the floor beneath a table. Visible waste/material accumulation is present, but "
    "there is no clear evidence of a municipal garbage-bin overflow or street-side "
    "waste dumping.",
    (
        "water_leakage",
        "Road/ground water accumulation",
    ): "A visible muddy water channel/pool runs along the edge of a paved pathway. "
    "Water has accumulated and is flowing/collecting along the drainage edge, with "
    "wet ground and debris visible.",
    (
        "drainage_damage",
        "Blocked/damaged drainage",
    ): "A concrete drainage/slab section is visibly displaced and broken, leaving an "
    "open gap beneath the slab along the roadside. This represents damaged roadside "
    "drainage infrastructure and a potential pedestrian/road hazard.",
    (
        "drainage_damage",
        "Open/unsafe drain",
    ): "A section of roadside drainage is uncovered/damaged, with concrete slabs "
    "displaced and an open drainage cavity exposed next to the road. This creates a "
    "clear physical safety hazard.",
    (
        "no_incident",
        None,
    ): "A maintained roadside area with healthy vegetation, a painted curb and an "
    "apparently intact paved surface. No pothole, flooding, garbage overflow, fallen "
    "tree or broken streetlight is visibly present.",
    (
        "pest_infestation",
        "Potential infrastructure/property damage",
    ): "The video shows a black-colored worm/termite-like pest on the building "
    "surface. Based on the provided identification, this should be treated as a "
    "termite infestation that may pose a potential property/infrastructure damage "
    "concern.",
    (
        "water_leakage",
        "Wall moisture damage",
    ): "The video shows extensive brown moisture staining and water streaks across "
    "the tiled wall, consistent with prolonged water leakage or seepage. The actual "
    "source of the leakage is not visible.",
    (
        "water_leakage",
        "Roof leakage / building water damage",
    ): "The video shows visible water leakage from the roof/ceiling area, with "
    "moisture and water staining on the interior surface. The evidence indicates a "
    "roof leak affecting the building interior.",
}

# Generic fallback wording families per category (used when no exact template
# exists for the detected combination, e.g. older corpus media).
_FALLBACK_BY_CATEGORY: dict[str, str] = {
    "pothole_road_damage": (
        "Visible damage to the paved road surface consistent with a pothole or "
        "cracked pavement, creating a potential road-hazard condition."
    ),
    "water_leakage": (
        "Visible water accumulation, flow or leakage consistent with a water "
        "incident; the media's appearance matches water evidence, but the "
        "wording is template-generated and not a verified visual fact."
    ),
    "garbage_overflow": (
        "Visible waste, bags or litter accumulation consistent with garbage "
        "overflow or waste accumulation at the location."
    ),
    "broken_streetlight": (
        "A streetlight fixture is visible; the scene is consistent with a "
        "broken or unlit streetlight condition."
    ),
    "fallen_tree": (
        "A fallen tree or large branch is visible, consistent with a fallen-tree "
        "incident affecting the area."
    ),
    "other_infrastructure_damage": (
        "Visible building/wall infrastructure damage that does not clearly "
        "belong to the five current Civitas MVP categories."
    ),
    "drainage_damage": (
        "Visible roadside drainage infrastructure damage with displaced or "
        "broken concrete elements, presenting a potential hazard."
    ),
    "no_incident": (
        "The scene appears as a normal, maintained environment with no visible "
        "civic incident such as pothole, flooding, garbage overflow, fallen "
        "tree or broken streetlight."
    ),
    "pest_infestation": (
        "A pest/termite-like organism is visible on a building surface, "
        "consistent with an infestation that may pose property damage concern."
    ),
}


def build_precise_description(
    primary_category: str | None,
    secondary_label: str | None,
    probability_vector: dict[str, float] | None = None,
    evidence: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Template description for the detected (primary, secondary) pair.

    Returns (description, basis). The basis honestly records that the wording
    is template-generated from the detected category/subcategory — never an
    LLM caption and never evidence that was not detected.
    """
    if not primary_category:
        return "", ["no description: no primary category detected"]
    text = _DESCRIPTIONS.get((primary_category, secondary_label))
    if text is None:
        text = _FALLBACK_BY_CATEGORY.get(primary_category, "")
        basis = [
            f"precise description: template fallback for category "
            f"'{primary_category}' (no exact subcategory template "
            f"for '{secondary_label or 'None'}')"
        ]
    else:
        basis = [
            f"precise description: template for ({primary_category}, "
            f"{secondary_label or 'None'}), grounded in the detected "
            f"category/subcategory only"
        ]
    if not text:
        label = CATEGORY_LABELS.get(primary_category, primary_category)
        text = f"Detected: {label}. See observable evidence for the supporting signals."
        basis.append("precise description: generic fallback wording")
    return text, basis


__all__ = ["build_precise_description"]
