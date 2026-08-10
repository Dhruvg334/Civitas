"""Train the vision-nn-v1 incident classifier.

Deterministic recipe (all seeds fixed):

  * Dataset: the synthetic Civitas benchmark scene grammar
    (`civitas_vision.benchmark.make_image`) with variants [default, flow]
    weighted [3, 1], train/test split by disjoint seed floors.
  * Model: ResNet18 initialized with ImageNet weights; fine-tune the
    final residual block (layer4) + the classification head only, so the
    ImageNet feature priors are preserved and training stays fast on CPU.
  * Augmentation (train only): random horizontal flip, small rotation,
    color jitter, random crop — cheap label-preserving transforms that
    reduce overfitting to exact synthetic pixel layouts.
  * OOD calibration: Mahalanobis distances of the training embeddings
    (standardized, 512-dim avgpool features) -> median stored in the
    model card; inference divides by this median (same semantics as the
    k-NN baseline's "distance / corpus median distance" ratio).

Outputs (gitignored artifacts, never committed):

  datasets/generated/vision/vision-nn-v1/model.pt
  datasets/generated/vision/vision-nn-v1/model_card.json

Run from the repo root:

  python ml/training/train_vision_nn.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "ml" / "vision" / "src"))

from civitas_vision.benchmark import make_image  # noqa: E402
from civitas_vision.contracts import CIVITAS_CATEGORIES  # noqa: E402

TRAIN_SEED = 11
TRAIN_PER_CLASS = 48
TEST_PER_CLASS = 24
EPOCHS = 10
BATCH_SIZE = 16
LR = 5e-4
WEIGHT_DECAY = 1e-4
IMAGE_SIZE = 224
VARIANT_POOL = ["default", "flow"]
VARIANT_WEIGHTS = [3, 1]

CLASSES = list(CIVITAS_CATEGORIES)
OUT_DIR = REPO_ROOT / "datasets" / "generated" / "vision" / "vision-nn-v1"


class SyntheticIncidentDataset(Dataset):
    """Deterministic synthetic scenes (train with augmentation flag)."""

    def __init__(self, seed_floor: int, n_per_class: int, *, train: bool) -> None:
        self._items: list[tuple[str, int, str]] = []
        rng = np.random.default_rng(TRAIN_SEED if train else TRAIN_SEED + 1)
        idx = 0
        for cat in CLASSES:
            for _ in range(n_per_class):
                variant = rng.choice(VARIANT_POOL, p=np.asarray(VARIANT_WEIGHTS) / sum(VARIANT_WEIGHTS))
                self._items.append((cat, seed_floor + idx, variant))
                idx += 1
        self._train = train

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, i: int) -> tuple[torch.Tensor, int]:
        cat, seed, variant = self._items[i]
        img = make_image(cat, seed, variant)
        label = CLASSES.index(cat)
        if self._train:
            img = TRAIN_AUG(img)  # type: ignore[arg-type]
        return TRANSFORMS(img), label


TRAIN_AUG = transforms.Compose(
    [
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(degrees=8),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
    ]
)
TRANSFORMS = transforms.Compose(
    [
        transforms.Resize(IMAGE_SIZE),
        transforms.CenterCrop(IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_model() -> nn.Module:
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, len(CLASSES))
    for param in model.parameters():
        param.requires_grad = False
    for param in model.layer4.parameters():
        param.requires_grad = True
    for param in model.fc.parameters():
        param.requires_grad = True
    return model


@torch.inference_mode()
def maha_median(model: nn.Module, loader: DataLoader) -> float:
    """Median standardized avgpool distance over the training set."""
    model.eval()
    embs: list[np.ndarray] = []
    for x, _ in loader:
        e = torch.flatten(model.avgpool(model.layer4(model.layer3(model.layer2(model.layer1(model.maxpool(model.relu(model.bn1(model.conv1(x))))))))), 1)
        embs.append(e.numpy())
    all_embs = np.vstack(embs)
    mean = all_embs.mean(axis=0)
    std = all_embs.std(axis=0)
    std[std < 1e-6] = 1.0
    z = (all_embs - mean) / std
    dists = np.linalg.norm(z, axis=1)
    return float(np.median(dists)), mean.tolist(), std.tolist()


@torch.inference_mode()
def evaluate(model: nn.Module, loader: DataLoader) -> tuple[float, list[list[int]]]:
    model.eval()
    matrix = np.zeros((len(CLASSES), len(CLASSES)), dtype=int)
    for x, y in loader:
        logits = model(x)
        pred = logits.argmax(dim=1)
        for t, p in zip(y.tolist(), pred.tolist()):
            matrix[t, p] += 1
    accuracy = float(np.trace(matrix) / max(matrix.sum(), 1))
    return accuracy, matrix.tolist()


def train() -> None:
    torch.manual_seed(TRAIN_SEED)
    np.random.seed(TRAIN_SEED)

    train_data = SyntheticIncidentDataset(seed_floor=100, n_per_class=TRAIN_PER_CLASS, train=True)
    test_data = SyntheticIncidentDataset(seed_floor=1000, n_per_class=TEST_PER_CLASS, train=False)
    train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True, generator=torch.Generator().manual_seed(TRAIN_SEED))
    test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False)

    model = load_model()
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=LR, weight_decay=WEIGHT_DECAY
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)
    criterion = nn.CrossEntropyLoss()

    best_acc, best_state = 0.0, None
    start = time.time()
    for epoch in range(EPOCHS):
        model.train()
        total_loss, n = 0.0, 0
        for x, y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(y)
            n += len(y)
        scheduler.step()
        acc, _ = evaluate(model, test_loader)
        print(f"epoch {epoch + 1}/{EPOCHS}: loss {total_loss / n:.4f}, holdout acc {acc:.4f}")
        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    model.load_state_dict(best_state)
    acc, matrix = evaluate(model, test_loader)
    median, emb_mean, emb_std = maha_median(model, train_loader)
    elapsed = time.time() - start

    tps = [matrix[i][i] for i in range(len(CLASSES))]
    supports = [sum(row) for row in matrix]
    per_class_acc = {c: round(tp / max(sup, 1), 4) for c, tp, sup in zip(CLASSES, tps, supports)}

    card = {
        "model_version": "vision-nn-v1",
        "architecture": "resnet18 (ImageNet init), fine-tuned layer4+fc",
        "train": {"per_class": TRAIN_PER_CLASS, "variants": VARIANT_POOL, "weights": VARIANT_WEIGHTS, "seed": TRAIN_SEED},
        "test": {"per_class": TEST_PER_CLASS, "seed_floor": 1000},
        "optimizer": {"name": "adamw", "lr": LR, "weight_decay": WEIGHT_DECAY, "epochs": EPOCHS, "batch_size": BATCH_SIZE},
        "holdout_accuracy": round(acc, 4),
        "holdout_per_class_accuracy": per_class_acc,
        "confusion_matrix": matrix,
        "ood_median_maha": round(median, 4),
        "embedding_mean": emb_mean,
        "embedding_std": emb_std,
        "training_seconds": round(elapsed, 1),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model_state": best_state, "card": card},
        OUT_DIR / "model.pt",
    )
    (OUT_DIR / "model_card.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    print(f"\nholdout accuracy {acc:.4f}")
    print(f"per-class accuracy: {per_class_acc}")
    print(f"confusion matrix (rows=true, cols=pred): {matrix}")
    print(f"OOD median Mahalanobis distance: {median:.4f}")
    print(f"saved -> {OUT_DIR}")


if __name__ == "__main__":
    train()