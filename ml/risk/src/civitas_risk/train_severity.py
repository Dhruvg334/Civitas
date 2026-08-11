"""Train the severity ML calibration artifact.

Usage:
    python -m civitas_risk.train_severity \
        --dataset ../datasets/generated/risk_samples.jsonl \
        --out ../artifacts/severity_coefficients.json

Reads the synthetic labeled dataset produced by
datasets/generators/generate_risk_dataset.py, fits the logistic calibrator
and writes a versioned coefficient artifact. Reported metrics come from the
training split only unless --heldout is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from civitas_risk.features import FEATURE_KEYS
from civitas_risk.ml_models import LogisticCalibrator


def load_samples(path: Path) -> tuple[list[list[float]], list[float]]:
    X: list[list[float]] = []
    y: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("kind") != "risk_sample":
            continue
        X.append([float(row["features"][k]) for k in FEATURE_KEYS])
        y.append(float(row["severity_label"]))
    return X, y


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent.parent.parent / "artifacts" / "severity_coefficients.json")
    parser.add_argument("--iterations", type=int, default=300)
    parser.add_argument("--heldout", type=float, default=0.2)
    args = parser.parse_args()

    X, y = load_samples(args.dataset)
    if not X:
        raise SystemExit("no labeled samples found in dataset")

    split = int(len(X) * (1.0 - args.heldout))
    train_x, train_y = X[:split], y[:split]
    test_x, test_y = X[split:], y[split:]

    model = LogisticCalibrator(feature_names=list(FEATURE_KEYS), iterations=args.iterations)
    model.fit(train_x, train_y)

    train_rmse = model.training_rmse_
    test_preds = model.predict_proba(test_x)
    test_rmse = (sum((p - t) ** 2 for p, t in zip(test_preds, test_y)) / len(test_y)) ** 0.5

    artifact = model.to_artifact()
    artifact.update(
        {
            "model_version": "severity-ml-v1",
            "dataset": str(args.dataset),
            "n_train": len(train_x),
            "n_test": len(test_x),
            "train_rmse": round(train_rmse or 0.0, 5),
            "heldout_rmse": round(test_rmse, 5),
        }
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(f"fitted logistic calibrator: train_rmse={train_rmse:.4f} "
          f"heldout_rmse={test_rmse:.4f} -> {args.out}")


if __name__ == "__main__":
    main()