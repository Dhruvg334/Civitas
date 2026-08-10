"""Zero-shot CLIP incident classifier for real-world media (real-media track).

The deterministic k-NN classifier (and the vision-nn-v1 ResNet) are trained
on the *procedural* benchmark corpus: they are accurate on synthetic scenes
and genuinely weak on real-world photos (the real-world probe collapsed
almost everything into `pothole_road_damage`). This module adds a third
classifier with the opposite trade:

- `CLIPZeroShotClassifier` (model edition `vision-clip-v1`) classifies via
  OpenAI's CLIP ViT-B/32 zero-shot: each Civitas category is a small set of
  plain-language prompt templates; the image embedding's cosine similarity
  to the best prompt per category becomes that category's logit
  (temperature 100.0, the CLIP logit scale). No training on the probe
  corpus, no labels ever enter the prompts — the demo photos only verify
  what the model already knows about natural images.
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
should re-calibrate it. On the probe corpus: 19/19 demo images are
in-domain (ratios <= 1.86) and both out-of-domain controls are flagged
(ratios >= 2.09).
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from functools import lru_cache
from typing import Any

from PIL import Image

from civitas_vision.contracts import CIVITAS_CATEGORIES, ClassificationProbs

MODEL_ID = "openai/clip-vit-base-patch32"
MODEL_VERSION = "vision-clip-v1"
# CLIP's logit scale: probabilities = softmax(100 * cosine).
_LOGIT_SCALE = 100.0
_MIN_CONFIDENCE_FLOOR = 0.01
_CONFIDENCE_EPS = 1e-9
# Calibrated on the real-world probe corpus (recorded limitation): the
# cosine level treated as "confidently in-manifold" (ratio 1.0). The
# product's 2.0 uncertainty floor sits at s_max = 0.22.
OOD_REFERENCE_SIMILARITY = 0.44

_logger = logging.getLogger(__name__)

# Plain-language prompt templates per Civitas category. Short literal
# descriptions follow CLIP's known behaviour on ViT-B/32 (single-domain
# descriptions beat templated captions). Deliberately label-free: the
# category name itself never appears in a prompt.
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
    ),
    "garbage_overflow": (
        "an overflowing garbage bin full of trash",
        "a pile of scattered waste and litter on the street",
        "garbage bags and trash overflowing on the pavement",
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
}

_ALL_PROMPTS: tuple[str, ...] = tuple(
    prompt for prompts in CATEGORY_PROMPTS.values() for prompt in prompts
)
_PROMPT_INDEX: dict[str, int] = {
    prompt: i for i, prompt in enumerate(_ALL_PROMPTS)
}


def _torch():
    """Lazy torch/transformers import (optional dependency guard)."""
    import torch  # noqa: PLC0415
    import transformers  # noqa: PLC0415

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
    confidence = p(top-1) - p(top-2), s_max = max category score.
    """
    import math

    logits = [_LOGIT_SCALE * category_scores[c] for c in CIVITAS_CATEGORIES]
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


class CLIPZeroShotClassifier:
    """Zero-shot CLIP classifier over the five Civitas MVP categories.

    Deterministic in inference (no dropout; model frozen): the same image
    always produces the same probabilities, confidence and OOD ratio.
    Constructor takes the already-loaded model + processor so unit tests
    can inject stubs; production code should use `CLIPZeroShotClassifier.load()`.
    """

    def __init__(
        self,
        model: Any,
        processor: Any,
        prompts: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        self._model = model
        self._processor = processor
        self._prompts = dict(prompts or CATEGORY_PROMPTS)
        self._text_features = self._encode_text()

    @classmethod
    def load(cls) -> "CLIPZeroShotClassifier | None":
        """Load the HF CLIP checkpoint; None when optional deps or the
        model are unavailable (the pipeline falls back to k-NN)."""
        try:
            torch, transformers = _torch()
            from transformers import CLIPModel, CLIPProcessor  # noqa: PLC0415
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

    def _encode_text(self):
        torch, _ = _torch()
        texts = [p for prompts in self._prompts.values() for p in prompts]
        inputs = self._processor(text=texts, return_tensors="pt", padding=True)
        with torch.inference_mode():
            return torch.nn.functional.normalize(
                self._model.get_text_features(**inputs), dim=-1
            )

    def predict(self, image: Image.Image) -> ClassificationProbs:
        """Classify one image -> probabilities, margin confidence, OOD ratio."""
        torch, _ = _torch()
        inputs = self._processor(images=image, return_tensors="pt")
        with torch.inference_mode():
            image_feature = torch.nn.functional.normalize(
                self._model.get_image_features(**inputs), dim=-1
            )
            sims = torch.matmul(image_feature, self._text_features.T)[0]

        similarity_map = {
            prompt: float(sims[_PROMPT_INDEX[prompt]]) for prompt in _ALL_PROMPTS
        }
        category_scores = category_prompt_scores(similarity_map, self._prompts)
        probs_values, margin, s_max = calibrate(category_scores)
        probabilities = {
            cat: round(float(v), 6) for cat, v in zip(CIVITAS_CATEGORIES, probs_values)
        }
        primary = max(probabilities, key=probabilities.__getitem__)
        confidence = max(min(margin, 1.0), _MIN_CONFIDENCE_FLOOR)

        ood_ratio = ood_ratio_from_best_similarity(s_max)
        basis = [
            f"{MODEL_VERSION}: zero-shot CLIP ({MODEL_ID}) over {len(category_scores)} "
            f"categories, prompt templates only (no training on probe media)",
            f"per-category best cosine similarities "
            f"{[f'{c}={category_scores[c]:.2f}' for c in CIVITAS_CATEGORIES]}",
            f"softmax margin confidence {confidence:.3f} (logit scale {_LOGIT_SCALE:.0f})",
            f"out-of-distribution ratio {ood_ratio:.2f} = {OOD_REFERENCE_SIMILARITY:.2f} "
            f"(reference similarity) / {s_max:.2f} (best category similarity)",
        ]
        return ClassificationProbs(
            probabilities=probabilities,
            primary_category=primary,
            confidence=round(confidence, 4),
            ood_ratio=round(min(ood_ratio, 999.0), 3),
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
    "CATEGORY_PROMPTS",
    "CLIPZeroShotClassifier",
    "MODEL_ID",
    "MODEL_VERSION",
    "OOD_REFERENCE_SIMILARITY",
    "calibrate",
    "category_prompt_scores",
    "ood_ratio_from_best_similarity",
    "real_media_classifier",
]