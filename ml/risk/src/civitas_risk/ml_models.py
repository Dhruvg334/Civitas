"""Small, dependency-free logistic regression for severity calibration.

Deliberately tiny: a single softmax/logistic layer trained with gradient
descent and L2 regularization. It exists so the ML calibration path can be
trained, versioned and evaluated without heavyweight dependencies; swapping
in scikit-learn later is a drop-in at the ServiceAdapters boundary.
"""

from __future__ import annotations

import math
import random
from typing import Sequence

from civitas_risk.features import FEATURE_KEYS


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


class LogisticCalibrator:
    """Logistic regression over the normalized feature vector (target [0,1])."""

    def __init__(
        self,
        feature_names: Sequence[str] = FEATURE_KEYS,
        learning_rate: float = 0.1,
        l2: float = 0.001,
        iterations: int = 300,
        seed: int = 42,
    ) -> None:
        self.feature_names = list(feature_names)
        self.coef_: list[float] = [0.0] * len(self.feature_names)
        self.intercept_: float = 0.0
        self.learning_rate = learning_rate
        self.l2 = l2
        self.iterations = iterations
        self.seed = seed
        self.fitted_ = False
        self.training_rmse_: float | None = None

    def _features(self, x: Sequence[float]) -> list[float]:
        if len(x) != len(self.feature_names):
            raise ValueError(
                f"expected {len(self.feature_names)} features, got {len(x)}"
            )
        return [max(0.0, min(1.0, float(v))) for v in x]

    def predict_proba(self, X: Sequence[Sequence[float]]) -> list[float]:
        """Sigmoid outputs in [0,1] for each row."""
        if not self.fitted_:
            raise RuntimeError("model not fitted; call fit() first")
        out: list[float] = []
        for row in X:
            z = self.intercept_ + sum(
                c * v for c, v in zip(self.coef_, self._features(row))
            )
            out.append(_sigmoid(z))
        return out

    def fit(self, X: Sequence[Sequence[float]], y: Sequence[float]) -> "LogisticCalibrator":
        """Batch gradient descent; y targets in [0,1] (regression objective)."""
        rows = [self._features(x) for x in X]
        targets = [max(0.0, min(1.0, float(t))) for t in y]
        if len(rows) != len(targets) or not rows:
            raise ValueError("X and y must be non-empty and aligned")
        rng = random.Random(self.seed)
        coef = [rng.uniform(-0.01, 0.01) for _ in self.feature_names]
        intercept = 0.0
        n = len(rows)
        for _ in range(self.iterations):
            grad_c = [0.0] * len(self.feature_names)
            grad_b = 0.0
            for x, t in zip(rows, targets):
                z = intercept + sum(c * v for c, v in zip(coef, x))
                p = _sigmoid(z)
                err = p - t
                for i, v in enumerate(x):
                    grad_c[i] += err * v
                grad_b += err
            for i in range(len(coef)):
                coef[i] -= self.learning_rate * (grad_c[i] / n + self.l2 * coef[i])
            intercept -= self.learning_rate * (grad_b / n)
        self.coef_ = coef
        self.intercept_ = intercept
        self.fitted_ = True
        self.training_rmse_ = math.sqrt(
            sum(
                (self.predict_proba([x])[0] - t) ** 2 for x, t in zip(rows, targets)
            )
            / n
        )
        return self

    def to_artifact(self) -> dict[str, object]:
        if not self.fitted_:
            raise RuntimeError("model not fitted")
        return {
            "feature_names": self.feature_names,
            "coefficients": self.coef_,
            "intercept": self.intercept_,
            "training_rmse": self.training_rmse_,
        }