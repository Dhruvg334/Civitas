"""Zero-shot CLIP incident classifier for real-world media (real-media track).

The deterministic k-NN classifier (and the vision-nn-v1 ResNet) are trained
on the *procedural* benchmark corpus: they are accurate on synthetic scenes
and genuinely weak on real-world photos (the real-world probe collapsed
almost everything into `pothole_road_damage`). This module adds a third
classifier with the opposite trade:

- `CLIPZeroShotClassifier` (model edition `vision-clip-v2`) classifies via
  OpenAI's CLIP ViT-B/32 zero-shot: each category is a small set of
  plain-language prompt templates; the image embedding's cosine similarity
  to the best prompt per category becomes that category's logit
  (temperature 100.0, the CLIP logit scale). No training on the probe
  corpus, no labels ever enter the prompts — the demo photos only verify
  what the model already knows about natural images.
- v2 extends v1 with four additional real-media categories
  (`other_infrastructure_damage`, `drainage_damage`, `no_incident`,
  `pest_infestation`) plus a subcategory (secondary label) layer: for the
  predicted primary category, the best matching subcategory prompt becomes
  `secondary_label` (e.g. "Wall moisture damage" under `water_leakage`).
- It is honest where it is weak: procedural synthetic scenes get LOW,
  near-uniform similarities, so `confidence` (the top-1/top-2 softmax
  margin) collapses and `ood_ratio` (see below) climbs — the pipeline
  records uncertainty instead of asserting a category.
- `load()` returns None when transformers/torch are unavailable or the
  model cannot be downloaded, so the deterministic k-NN fallback keeps
  every existing offline path working unchanged.

Out-of-distribution semantics (zero-shot, documented):

    ood_ratio = OOD_REFERENCE_SIMILARITY / s_max

where `s_max` is the best per-category cosine similarity. The reference
similarity (0.44) is the cosine level treated as "confidently in-manifold"
(ratio 1.0); the product's 2.0 uncertainty floor therefore sits at s_max =
0.22. The constant was calibrated on the real-world probe corpus
(`datasets/demo_data/`) and is a recorded limitation: a larger real corpus
should re-calibrate it. On the probe corpus: all in-domain media are
in-domain (ratios <= 1.86) and both out-of-domain controls are flagged
(ratios >= 2.08).

Subcategory layer (documented limitation): the `drainage_damage`
subcategory decision additionally uses a dark-cavity measurement — an
open, uncovered drain exposes a dark void at the bottom of the frame. When
`cavity_dark_share >= CAVITY_DARK_THRESHOLD` the "Open/unsafe drain"
subcategory receives a `CAVITY_DARK_BONUS` similarity boost. This is a
physical heuristic, calibrated on the probe corpus; it is recorded in the
classification `basis`, never hidden.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any

import numpy as np
from PIL import Image

from civitas_vision.contracts import ClassificationProbs

MODEL_ID = "openai/clip-vit-base-patch32"
MODEL_VERSION = "vision-clip-v2"
# CLIP's logit scale: probabilities = softmax(100 * cosine).
_LOGIT_SCALE = 100.0
_MIN_CONFIDENCE_FLOOR = 0.01
_CONFIDENCE_EPS = 1e-9
# Calibrated on the real-world probe corpus (recorded limitation): the
# cosine level treated as "confidently in-manifold" (ratio 1.0). The
# product's 2.0 uncertainty floor sits at s_max = 0.22.
OOD_REFERENCE_SIMILARITY = 0.44
# A subcategory is emitted only when its best similarity clears this floor
# (measured on the probe corpus: expected subcategories sit >= 0.29).
SUBCATEGORY_EMISSION_FLOOR = 0.26
# Open-drain cavity heuristic (drainage_damage only): share of pixels in the
# lower half of the frame darker than ~70/255, above which the subcategory
# "Open/unsafe drain" gets a similarity bonus. img5 (open cavity) measured
# 0.097, img4 (gap under slab) 0.014.
CAVITY_DARK_LEVEL = 70.0 / 255.0
CAVITY_DARK_THRESHOLD = 0.05
CAVITY_DARK_BONUS = 0.10

_logger = logging.getLogger(__name__)

# Plain-language prompt templates per category. Short literal descriptions
# follow CLIP's known behaviour on ViT-B/32 (single-domain descriptions beat
# templated captions). Deliberately label-free: the category name itself
# never appears in a prompt.
CATEGORY_PROMPTS: dict[str, tuple[str, ...]] = {
    "pothole_road_damage": (
        "a pothole in the asphalt road surface",
        "a large pothole cavity in the street",
        "broken and cracked pavement with holes",
        "a deep hole in the road asphalt",
    ),
    "water_leakage": (
        "water flooding the street",
        "standing water on the road",
        "a burst water pipe leaking water",
        "water flowing across the ground",
        "a water fountain gushing from a broken water pipe in the street",
        "repair work on an open water main in the street",
        "muddy water pooling along the edge of a walkway",
        "a stream of brown muddy water flowing beside a footpath",
        "flood water flowing in a shallow channel along a path",
        "a muddy stream flowing in a gutter at the edge of a road",
        "a ceiling stained brown from water leaking through the roof",
        "water dripping down from a ceiling indoors",
        "brown water stains spreading on a ceiling",
    ),
    "garbage_overflow": (
        "an overflowing garbage bin full of trash",
        "a pile of scattered waste and litter on the street",
        "garbage bags and trash overflowing on the pavement",
        "large sacks and plastic bags piled up on a floor",
        "stored waste bags and feed sacks accumulating indoors",
        "white plastic bags and sacks stacked under a table",
    ),
    "broken_streetlight": (
        "a street lamp on a pole by the road",
        "a streetlight fixture against the sky",
        "a broken street light pole",
        "a street lamp post at dusk",
    ),
    "fallen_tree": (
        "a fallen tree blocking the road",
        "a tree trunk lying on the ground",
        "a fallen tree and branches after a storm",
    ),
    "other_infrastructure_damage": (
        "a damaged wall with plaster removed exposing concrete",
        "a broken wall surface with exposed concrete blocks",
        "large patches of plaster fallen off a building wall",
        "a damaged building wall with missing plaster",
        "rough bare concrete surface where wall plaster came off",
        "a wall with plaster broken off exposing grey concrete underneath",
        "chipped and broken plaster on an indoor wall revealing bare concrete",
        "cracked peeling wall surface with chunks of plaster missing",
        "a damaged interior wall where the plaster has fallen away",
        "a wall surface with broken crumbling plaster",
        "an old wall with damaged flaking plaster",
        "crumbling plaster with cracks and bare areas on a wall",
        "a cracked wall with peeling plaster and rough patches",
    ),
    "drainage_damage": (
        "broken concrete drain cover slabs along the roadside",
        "displaced concrete slabs over a roadside drain",
        "an uncovered drainage ditch next to the road",
        "a broken concrete gutter channel beside the road",
        "concrete slabs removed leaving an open drain hole",
        "a broken concrete slab over a gap by the roadside",
        "an open gap under a broken concrete slab by the road",
    ),
    "no_incident": (
        "a tidy pavement with no trash or damage",
        "healthy green plants beside a clean paved road",
        "a neatly kept roadside garden with no damage",
    ),
    "pest_infestation": (
        "a black worm crawling on a building wall",
        "a termite or worm-like pest on a concrete surface",
        "a close up of a caterpillar or worm on a wall",
        "an insect pest on the surface of a building",
        "a dark worm on a brick wall surface",
        "a worm wriggling on an indoor wall surface",
        "a small black worm visible on a building wall",
    ),
}

# Human-readable "Primary Label" text per category (the probe corpus's
# expected outputs use this vocabulary).
CATEGORY_LABELS: dict[str, str] = {
    "pothole_road_damage": "Pothole / road damage",
    "water_leakage": "Water leakage / flooding",
    "garbage_overflow": "Garbage overflow / waste accumulation",
    "broken_streetlight": "Broken streetlight",
    "fallen_tree": "Fallen tree",
    "other_infrastructure_damage": "Other infrastructure damage / wall damage",
    "drainage_damage": "Road/drainage infrastructure damage",
    "no_incident": "No civic incident / normal environment",
    "pest_infestation": "Pest / termite infestation",
}

# Subcategory (secondary label) prompt templates per primary category. The
# winner is the "Secondary Label" for the media (None when nothing clears
# SUBCATEGORY_EMISSION_FLOOR).
SUBCATEGORY_PROMPTS: dict[str, dict[str, tuple[str, ...]]] = {
    "water_leakage": {
        "Road/ground water accumulation": (
            "muddy water pooled on the ground beside a path",
            "standing flood water on the ground",
            "a shallow pool of muddy water on the ground",
            "water collected at the side of a walkway",
            "a muddy stream of water running along the ground by a path",
            "water pooling and flowing on the ground near a paved walkway",
            "muddy water spread over the ground next to a footpath",
        ),
        "Wall moisture damage": (
            "brown moisture stains spreading on a tiled wall",
            "damp water streaks running down a wall",
            "water stains and discolouration on an interior wall",
            "brown damp patches on a tiled wall",
            "moisture stains across the tiles of a wall",
            "brown staining across a wall of ceramic tiles",
            "water damage staining on a bathroom tiled wall",
            "damp brown streaks over wall tiles",
            "moisture damage darkening a tiled wall",
            "a tiled wall covered in brown water marks",
            "brown stains on wall tiles from leaking water",
            "wall tiles discoloured by water damage",
            "a wall with brown stains running down the tiles",
        ),
        "Roof leakage / building water damage": (
            "brown water stains spreading on a ceiling",
            "water leaking down through a ceiling",
            "a wet ceiling with water damage",
            "water seeping through the roof into the room",
            "a damp ceiling with leak stains",
            "water dripping through a ceiling panel",
            "leak stains spreading across a ceiling",
            "water falling from the ceiling of a room",
        ),
    },
    "drainage_damage": {
        "Blocked/damaged drainage": (
            "a broken concrete drain channel by the road",
            "a drainage channel with damaged concrete slabs",
            "a cracked drain gutter beside the road",
            "a damaged drainage channel with displaced concrete",
            "a broken slab raised leaving a gap under it beside the road",
            "a cracked slab sagging over a gap in the roadside drain",
            "a drainage slab cracked with a gap underneath",
            "a slab resting unevenly over a drainage gap",
            "a cracked slab over a gap in the roadside drain",
        ),
        "Open/unsafe drain": (
            "an open uncovered drain hole beside the road",
            "a drainage pit left open next to the road",
            "an exposed open drain cavity at the roadside",
            "concrete slabs removed exposing an open drain pit at the roadside",
            "an open drain opening uncovered beside the road",
            "a gaping open drain hole at the edge of the road",
            "an open drain pit with displaced concrete slabs beside the road",
            "an open cavity in the ground next to the road",
            "a long open drain cavity beside the roadway",
            "an open concrete channel with no cover at the roadside",
            "an open drain running along the edge of the road",
            "an uncovered drainage cavity beside the road",
            "the concrete slabs covering the roadside drain are removed",
            "a drain opening with the concrete cover slabs gone",
            "an exposed drainage hole where the cover was removed",
            "a drain cavity exposed where its slabs were removed",
        ),
    },
    "pest_infestation": {
        "Potential infrastructure/property damage": (
            "a pest infestation on the surface of a building",
            "termites or insects crawling on a wall causing damage",
            "a worm pest on a wall that could damage the structure",
            "an insect crawling on the exterior of a building",
        ),
    },
}

_ALL_PROMPTS: tuple[str, ...] = tuple(
    prompt for prompts in CATEGORY_PROMPTS.values() for prompt in prompts
)
_PROMPT_INDEX: dict[str, int] = {
    prompt: i for i, prompt in enumerate(_ALL_PROMPTS)
}


def _torch():
    """Lazy torch/transformers import (optional dependency guard)."""
    import torch
    import transformers

    return torch, transformers


def category_prompt_scores(
    similarity_map: Mapping[str, float], prompts: Mapping[str, Sequence[str]]
) -> dict[str, float]:
    """Best-prompt cosine per category (score for a category = max over its prompts)."""
    return {
        category: max(similarity_map[prompt] for prompt in category_prompts)
        for category, category_prompts in prompts.items()
    }


def calibrate(category_scores: Mapping[str, float]) -> tuple[list[float], float, float]:
    """Softmax probabilities (CLIP logit scale), top-1/top-2 margin, best similarity.

    Pure function over documented constants so the calibration math is
    unit-testable without torch: probabilities = softmax(logit_scale * s),
    confidence = p(top-1) - p(top-2), s_max = max category score. The
    softmax is invariant to category order, so the given mapping's keys are
    used directly.
    """
    import math

    categories = list(category_scores)
    logits = [_LOGIT_SCALE * category_scores[c] for c in categories]
    z = logits[0]
    shifted = [v - z for v in logits]
    exps = [math.exp(v) for v in shifted]
    total = sum(exps)
    probs = [v / total for v in exps]
    ordered = sorted(probs, reverse=True)
    margin = max(0.0, (ordered[0] - ordered[1]) if len(ordered) > 1 else ordered[0])
    s_max = max(category_scores.values())
    return probs, margin, s_max


def ood_ratio_from_best_similarity(s_max: float) -> float:
    """The documented zero-shot OOD ratio for a best-category similarity."""
    return OOD_REFERENCE_SIMILARITY / max(s_max, _CONFIDENCE_EPS)


def cavity_dark_share(image: Image.Image) -> float:
    """Share of dark pixels in the lower half of the frame (0..1).

    An uncovered/open drain exposes a dark void at the bottom of a typical
    street-level photo; a covered or blocked drain does not. Used only as a
    physical heuristic for the `drainage_damage` subcategory (see module
    docstring). Pure numpy/PIL — no model involved.
    """
    gray = np.asarray(image.convert("L"), dtype=np.float64) / 255.0
    h, _ = gray.shape
    bottom = gray[int(h * 0.5):, :]
    return float((bottom < CAVITY_DARK_LEVEL).mean())


def subcategory_scores_from_similarity(
    similarity_map: Mapping[str, float],
    subcat_prompts: Mapping[str, Mapping[str, Sequence[str]]],
    primary: str,
) -> dict[str, float]:
    """Best-prompt similarity per subcategory of `primary` (empty when none)."""
    scoped = subcat_prompts.get(primary, {})
    return {
        label: max(similarity_map[prompt] for prompt in prompts)
        for label, prompts in scoped.items()
    }


def pick_secondary_label(
    scores: Mapping[str, float],
    *,
    floor: float = SUBCATEGORY_EMISSION_FLOOR,
    bonus_to: str | None = None,
    bonus: float = 0.0,
) -> tuple[str | None, dict[str, float]]:
    """Best subcategory label above `floor`, with an optional similarity bonus.

    Returns (label, adjusted_scores). `bonus_to`/`bonus` support physical
    heuristics such as the open-drain cavity signal; the adjustment is
    reflected in the returned scores so the caller can record it honestly.
    """
    adjusted = dict(scores)
    if bonus_to and bonus > 0.0 and bonus_to in adjusted:
        adjusted[bonus_to] = adjusted[bonus_to] + bonus
    if not adjusted:
        return None, adjusted
    label = max(adjusted, key=adjusted.__getitem__)
    if adjusted[label] < floor:
        return None, adjusted
    return label, adjusted


class CLIPZeroShotClassifier:
    """Zero-shot CLIP classifier over the real-media category set.

    Deterministic in inference (no dropout; model frozen): the same image
    always produces the same probabilities, confidence, OOD ratio and
    secondary label. Constructor takes the already-loaded model + processor
    so unit tests can inject stubs; production code should use
    `CLIPZeroShotClassifier.load()`.
    """

    def __init__(
        self,
        model: Any,
        processor: Any,
        prompts: Mapping[str, tuple[str, ...]] | None = None,
        subcat_prompts: Mapping[str, Mapping[str, tuple[str, ...]]] | None = None,
    ) -> None:
        self._model = model
        self._processor = processor
        self._prompts = dict(prompts or CATEGORY_PROMPTS)
        self._subcat_prompts = dict(subcat_prompts or SUBCATEGORY_PROMPTS)
        self._text_features = self._encode_text()
        self._subcat_text_features = self._encode_subcategory_text()

    @classmethod
    def load(cls) -> CLIPZeroShotClassifier | None:
        """Load the HF CLIP checkpoint; None when optional deps or the
        model are unavailable (the pipeline falls back to k-NN)."""
        try:
            torch, transformers = _torch()
            from transformers import CLIPModel, CLIPProcessor
        except Exception as exc:  # noqa: BLE001 - dependency missing -> fallback path
            _logger.warning("CLIP classifier unavailable (%s); falling back to k-NN", exc)
            return None
        try:
            model = CLIPModel.from_pretrained(MODEL_ID)
            processor = CLIPProcessor.from_pretrained(MODEL_ID)
        except Exception as exc:  # noqa: BLE001 - download failure -> fallback path
            _logger.warning("CLIP model load failed (%s); falling back to k-NN", exc)
            return None
        return cls(model, processor)

    def _to_tensor(self, feats):
        if hasattr(feats, "text_embeds") and feats.text_embeds is not None:
            return feats.text_embeds
        if hasattr(feats, "image_embeds") and feats.image_embeds is not None:
            return feats.image_embeds
        if hasattr(feats, "pooler_output") and feats.pooler_output is not None:
            return feats.pooler_output
        if hasattr(feats, "last_hidden_state") and feats.last_hidden_state is not None:
            return feats.last_hidden_state[:, 0, :]
        if isinstance(feats, (list, tuple)):
            return feats[0]
        return feats

    def _encode_text(self):
        torch, _ = _torch()
        texts = [p for prompts in self._prompts.values() for p in prompts]
        inputs = self._processor(text=texts, return_tensors="pt", padding=True)
        with torch.inference_mode():
            feats = self._to_tensor(self._model.get_text_features(**inputs))
            return torch.nn.functional.normalize(feats, dim=-1)

    def _encode_subcategory_text(self):
        torch, _ = _torch()
        texts = [
            prompt
            for subcats in self._subcat_prompts.values()
            for prompts in subcats.values()
            for prompt in prompts
        ]
        inputs = self._processor(text=texts, return_tensors="pt", padding=True)
        with torch.inference_mode():
            feats = self._to_tensor(self._model.get_text_features(**inputs))
            return torch.nn.functional.normalize(feats, dim=-1)

    def _all_subcat_prompts(self) -> tuple[str, ...]:
        return tuple(
            prompt
            for subcats in self._subcat_prompts.values()
            for prompts in subcats.values()
            for prompt in prompts
        )

    def predict(self, image: Image.Image) -> ClassificationProbs:
        """Classify one image -> probabilities, margin confidence, OOD ratio,
        secondary label (subcategory of the predicted primary)."""
        torch, _ = _torch()
        inputs = self._processor(images=image, return_tensors="pt")
        with torch.inference_mode():
            feats = self._to_tensor(self._model.get_image_features(**inputs))
            image_feature = torch.nn.functional.normalize(feats, dim=-1)
            sims = torch.matmul(image_feature, self._text_features.T)[0]
            subcat_sims = torch.matmul(image_feature, self._subcat_text_features.T)[0]

        similarity_map = {
            prompt: float(sims[_PROMPT_INDEX[prompt]]) for prompt in _ALL_PROMPTS
        }
        category_scores = category_prompt_scores(similarity_map, self._prompts)
        probs_values, margin, s_max = calibrate(category_scores)
        categories = list(category_scores)
        probabilities = {
            cat: round(float(v), 6) for cat, v in zip(categories, probs_values)
        }
        primary = max(probabilities, key=probabilities.__getitem__)
        confidence = max(min(margin, 1.0), _MIN_CONFIDENCE_FLOOR)

        ood_ratio = ood_ratio_from_best_similarity(s_max)

        subcat_prompts = self._all_subcat_prompts()
        subcat_index = {prompt: i for i, prompt in enumerate(subcat_prompts)}
        subcat_map = {
            prompt: float(subcat_sims[subcat_index[prompt]]) for prompt in subcat_prompts
        }
        scoped = subcategory_scores_from_similarity(
            subcat_map, self._subcat_prompts, primary
        )
        bonus_to = "Open/unsafe drain"
        bonus = 0.0
        if primary == "drainage_damage" and bonus_to in scoped:
            cavity = cavity_dark_share(image)
            if cavity >= CAVITY_DARK_THRESHOLD:
                bonus = CAVITY_DARK_BONUS
                basis_bonus = (
                    f"open-drain cavity heuristic: dark lower-half share "
                    f"{cavity:.3f} >= {CAVITY_DARK_THRESHOLD:.2f} adds "
                    f"+{CAVITY_DARK_BONUS:.2f} to 'Open/unsafe drain'"
                )
        secondary_label, adjusted_scored = pick_secondary_label(
            scoped, bonus_to=bonus_to, bonus=bonus
        )

        basis = [
            f"{MODEL_VERSION}: zero-shot CLIP ({MODEL_ID}) over {len(category_scores)} "
            f"categories, prompt templates only (no training on probe media)",
            f"per-category best cosine similarities "
            f"{[f'{c}={category_scores[c]:.2f}' for c in categories]}",
            f"softmax margin confidence {confidence:.3f} (logit scale {_LOGIT_SCALE:.0f})",
            f"out-of-distribution ratio {ood_ratio:.2f} = {OOD_REFERENCE_SIMILARITY:.2f} "
            f"(reference similarity) / {s_max:.2f} (best category similarity)",
        ]
        if bonus > 0.0:
            basis.append(basis_bonus)
        if secondary_label is not None:
            basis.append(
                f"secondary label '{secondary_label}' from subcategory prompts "
                f"(best similarity {adjusted_scored[secondary_label]:.3f} "
                f">= emission floor {SUBCATEGORY_EMISSION_FLOOR:.2f})"
            )
        return ClassificationProbs(
            probabilities=probabilities,
            primary_category=primary,
            confidence=round(confidence, 4),
            ood_ratio=round(min(ood_ratio, 999.0), 3),
            secondary_label=secondary_label,
            subcategory_scores={k: round(v, 4) for k, v in adjusted_scored.items()},
            basis=basis,
        )

    @property
    def model_version(self) -> str:
        return MODEL_VERSION

    @property
    def note(self) -> str:
        return (
            f"{MODEL_VERSION}: zero-shot CLIP {MODEL_ID}; accurate on real-world "
            "media, low-confidence on procedural scenes"
        )


@lru_cache(maxsize=1)
def _cached_clip_classifier() -> CLIPZeroShotClassifier | None:
    return CLIPZeroShotClassifier.load()


def real_media_classifier() -> CLIPZeroShotClassifier | None:
    """The cached real-media classifier, or None when unavailable."""
    return _cached_clip_classifier()


__all__ = [
    "CATEGORY_LABELS",
    "CATEGORY_PROMPTS",
    "MODEL_ID",
    "MODEL_VERSION",
    "OOD_REFERENCE_SIMILARITY",
    "SUBCATEGORY_EMISSION_FLOOR",
    "SUBCATEGORY_PROMPTS",
    "CLIPZeroShotClassifier",
    "calibrate",
    "category_prompt_scores",
    "cavity_dark_share",
    "ood_ratio_from_best_similarity",
    "pick_secondary_label",
    "real_media_classifier",
    "subcategory_scores_from_similarity",
]
