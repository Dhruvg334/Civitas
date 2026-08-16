"""Neural incident classifier (vision-nn-v1).

A fine-tuned ResNet18 (ImageNet-initialized) over the deterministic
synthetic benchmark set, with margin-based confidence and a calibrated
Mahalanobis out-of-distribution score.

Motivation over the k-NN baseline: the 16-feature classical vector cannot
separate "dark textured blob" categories in real photos (the real-world
probe collapsed almost everything into pothole_road_damage at confidence
~1.0). The ImageNet initialization supplies real-world texture/shape
priors; the synthetic set still defines the *decision surface* for the
five Civitas categories, so the recorded limitation (no real photo
labels) remains and is surfaced by the OOD gate.

Artifacts (weights + model card JSON) live under
`datasets/generated/vision/vision-nn-v1/`; the model card records
measured holdout metrics and the calibrated OOD median — nothing in this
module claims real-photo accuracy.

Public entry points:

    NNClassifier.load(weights_dir) -> NNClassifier | None

    Returns None when the checkpoint is missing, so the pipeline can
    fall back to the k-NN baseline without crashing (torch is an
    optional import: civitas_vision imports fine without it).
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from civitas_vision.contracts import CIVITAS_CATEGORIES, ClassificationProbs

MODEL_VERSION = "vision-nn-v1"
ARTIFACT_DIR_NAME = MODEL_VERSION
_MIN_CONFIDENCE_FLOOR = 0.01
_TEMPERATURE = 2.0


def _torch():
    """Lazy torch/torchvision import (optional dependency guard)."""
    import torch
    import torchvision

    return torch, torchvision


def default_weights_dir() -> Path:
    """Checkpoint directory under the gitignored generated-artifacts tree."""
    repo_root = Path(__file__).resolve().parents[4]
    return repo_root / "datasets" / "generated" / "vision" / ARTIFACT_DIR_NAME


def _checkpoint_path(weights_dir: Path) -> Path:
    return Path(weights_dir) / "model.pt"


def _card_path(weights_dir: Path) -> Path:
    return Path(weights_dir) / "model_card.json"


class NNClassifier:
    """ResNet18 incident classifier with honest confidence + OOD scoring.

    `confidence` is the softmax margin (top-1 minus top-2 probability at
    temperature 2.0): a scene that genuinely straddles categories
    collapses toward 0, a unanimous one approaches 1.
    `ood_ratio` is the input's Mahalanobis distance in the standardized
    embedding space divided by the median training Mahalanobis distance —
    the same "distance / corpus median" semantics as the k-NN baseline,
    so the product-level 2.0 uncertainty floor applies unchanged.
    """

    def __init__(self, model, card: dict[str, object]) -> None:
        self._model = model
        self._card = card
        self._median_maha = float(card.get("ood_median_maha", 1.0))
        self._device = next(model.parameters()).device

    @classmethod
    def load(cls, weights_dir: Path | None = None) -> NNClassifier | None:
        """Load the checkpoint; None when missing (pipeline falls back)."""
        weights_dir = Path(weights_dir) if weights_dir else default_weights_dir()
        ckpt = _checkpoint_path(weights_dir)
        card_path = _card_path(weights_dir)
        if not ckpt.exists() or not card_path.exists():
            return None
        try:
            torch, torchvision = _torch()
        except Exception:  # noqa: BLE001 - torch absent -> fallback path
            return None
        model = torchvision.models.resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, len(CIVITAS_CATEGORIES))
        state = torch.load(ckpt, map_location="cpu", weights_only=True)
        model.load_state_dict(state["model_state"])
        model.eval()
        card = json.loads(card_path.read_text(encoding="utf-8"))
        return cls(model, card)

    def predict(self, image: Image.Image) -> ClassificationProbs:
        """Classify one PIL image -> probabilities, margin, OOD ratio."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        torch, torchvision = _torch()
        tf = torchvision.transforms.Compose(
            [
                torchvision.transforms.Resize(256),
                torchvision.transforms.CenterCrop(224),
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )
        x = tf(image).unsqueeze(0)
        with torch.inference_mode():
            logits = self._model(x)
            probs = torch.softmax(logits / _TEMPERATURE, dim=1)[0]
            embedding = self._embedding(x)

        values = probs.tolist()
        probabilities = {
            cat: round(float(v), 6) for cat, v in zip(CIVITAS_CATEGORIES, values)
        }
        primary = max(probabilities, key=probabilities.__getitem__)
        ordered = sorted(probabilities.values(), reverse=True)
        margin = max(0.0, (ordered[0] - ordered[1]) if len(ordered) > 1 else ordered[0])
        confidence = max(min(margin, 1.0), _MIN_CONFIDENCE_FLOOR)

        ood_ratio = self._ood_ratio(embedding)
        basis = [
            "vision-nn-v1: ResNet18 (ImageNet init) fine-tuned on synthetic Civitas set",
            f"softmax margin confidence {confidence:.3f} (T={_TEMPERATURE})",
            f"Mahalanobis OOD ratio {ood_ratio:.2f} (median train distance {self._median_maha:.3f})",
        ]
        return ClassificationProbs(
            probabilities=probabilities,
            primary_category=primary,
            confidence=round(confidence, 4),
            ood_ratio=round(ood_ratio, 3),
            basis=basis,
        )

    def _embedding(self, x):
        """512-dim penultimate (avgpool) features for OOD scoring."""
        torch = _torch()[0]
        model = self._model
        with torch.inference_mode():
            x = model.conv1(x)
            x = model.bn1(x)
            x = model.relu(x)
            x = model.maxpool(x)
            x = model.layer1(x)
            x = model.layer2(x)
            x = model.layer3(x)
            x = model.layer4(x)
            x = model.avgpool(x)
            emb = torch.flatten(x, 1)
        return emb

    def _ood_ratio(self, embedding) -> float:
        """Mahalanobis distance (standardized dims) / median training distance."""
        torch = _torch()[0]
        mean = torch.tensor(self._card["embedding_mean"], dtype=embedding.dtype)
        std = torch.tensor(self._card["embedding_std"], dtype=embedding.dtype)
        std = torch.where(std < 1e-6, torch.ones_like(std), std)
        z = (embedding - mean) / std
        maha = float(torch.norm(z, dim=1)[0])
        return maha / max(self._median_maha, 1e-9)

    @property
    def model_version(self) -> str:
        return MODEL_VERSION

    @property
    def note(self) -> str:
        return (
            "vision-nn-v1: ResNet18 (ImageNet init), fine-tuned on synthetic "
            "Civitas set; margin confidence + Mahalanobis OOD"
        )


__all__ = ["MODEL_VERSION", "NNClassifier", "default_weights_dir"]