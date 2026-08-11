"""Vision model selection for the ML service (real-media track).

The service composes `VisualIntelligencePipeline`s; which classifier runs
is a *configuration decision*, deliberately not implicit:

    CIVITAS_VISION_MODEL   knn | clip        (default: knn)

- `knn`  (default): the deterministic k-NN over classical features, trained
  on the procedural benchmark corpus. Accurate on the synthetic manifold;
  weak on real-world photos. This is the default so the frozen Phase 11/12
  evaluation, the golden evidence trail and every offline path keep their
  exact, reproducible numbers with zero external dependencies.
- `clip` : the zero-shot CLIP classifier (`civitas_vision.clip_classifier`,
  edition `vision-clip-v2`) — nine real-media categories with per-subcategory
  evidence prompts, trained for accuracy on real-world natural photos, which
  is the media citizens actually upload. Requires `transformers` + torch
  and one HuggingFace download (`openai/clip-vit-base-patch32`). When the
  model cannot be loaded the service degrades to the k-NN with a recorded
  basis note — it never guesses and never crashes.

The real-world probe (`civitas_evaluation.real_world_probe`) and any API
deployment serving citizen media should select `clip`.
"""

from __future__ import annotations

import logging
import os

from civitas_vision.detector import VisualIntelligencePipeline

CID = "vision-clip-v2"
KID = "vision-knn-v1"

MODEL_KNN = "knn"
MODEL_CLIP = "clip"
_MODELS = (MODEL_KNN, MODEL_CLIP)

_logger = logging.getLogger(__name__)


def build_vision_pipeline(
    model: str | None = None,
) -> tuple[VisualIntelligencePipeline, str]:
    """Build the vision pipeline for the requested model.

    Returns (pipeline, model_version). `model` is one of 'knn' | 'clip';
    default comes from the CIVITAS_VISION_MODEL environment variable
    ('knn' when unset). A clip request that cannot be served (missing
    dependencies / download failure) degrades to the deterministic k-NN —
    the returned version string reports what actually runs.
    """
    requested = (model or os.environ.get("CIVITAS_VISION_MODEL", MODEL_KNN)).strip().lower()
    if requested not in _MODELS:
        # Unknown selection is a configuration error surfaced loudly,
        # never silently resolved to a different model.
        raise ValueError(
            f"CIVITAS_VISION_MODEL must be one of {_MODELS}, got {requested!r}"
        )
    if requested == MODEL_CLIP:
        from civitas_vision.clip_classifier import real_media_classifier

        classifier = real_media_classifier()
        if classifier is not None:
            return VisualIntelligencePipeline(classifier=classifier), classifier.model_version
        _logger.warning(
            "CIVITAS_VISION_MODEL=clip requested but the CLIP model is unavailable; "
            "degrading to the deterministic k-NN"
        )
    from civitas_vision.benchmark import train_default_model

    return VisualIntelligencePipeline(classifier=train_default_model()), KID


__all__ = [
    "KID",
    "MODEL_CLIP",
    "MODEL_KNN",
    "build_vision_pipeline",
]