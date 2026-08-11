"""Small, auditable metric helpers (no external stats dependencies).

Every formula is textbook: accuracy, precision, recall, F1, Cohen's
kappa for agreement, and confusion matrices. Nothing here is estimated or
guessed — each metric is computed from saved predictions over the frozen
test set.
"""

from __future__ import annotations

from civitas_evaluation.contracts import ClassMetrics, ConfusionMatrixRecord


def confusion_matrix(
    labels: list[str], predictions: list[str], classes: list[str]
) -> ConfusionMatrixRecord:
    index = {c: i for i, c in enumerate(classes)}
    matrix = [[0] * len(classes) for _ in classes]
    for label, pred in zip(labels, predictions):
        matrix[index[label]][index[pred]] += 1
    return ConfusionMatrixRecord(
        classes=list(classes),
        matrix=matrix,
        row_sums=[sum(row) for row in matrix],
    )


def per_class_metrics(cm: ConfusionMatrixRecord) -> list[ClassMetrics]:
    out: list[ClassMetrics] = []
    n_classes = len(cm.classes)
    for i, class_name in enumerate(cm.classes):
        tp = cm.matrix[i][i]
        col_sum = sum(cm.matrix[r][i] for r in range(n_classes)) or 0
        row_sum = cm.row_sums[i] or 0
        precision = tp / col_sum if col_sum else None
        recall = tp / row_sum if row_sum else None
        f1 = (
            (2 * precision * recall / (precision + recall))
            if precision is not None and recall is not None and (precision + recall) > 0
            else None
        )
        out.append(
            ClassMetrics(
                class_name=class_name,
                tp=tp,
                fp=col_sum - tp,
                fn=row_sum - tp,
                precision=round(precision, 4) if precision is not None else None,
                recall=round(recall, 4) if recall is not None else None,
                f1=round(f1, 4) if f1 is not None else None,
            )
        )
    return out


def macro_f1(class_wise: list[ClassMetrics]) -> float:
    scores = [c.f1 for c in class_wise if c.f1 is not None]
    return round(sum(scores) / len(scores), 4) if scores else 0.0


def accuracy(labels: list[str], predictions: list[str]) -> float:
    if not labels:
        return 0.0
    return round(sum(label == p for label, p in zip(labels, predictions)) / len(labels), 4)


def binary_prf(
    tp: int, fp: int, fn: int
) -> tuple[float | None, float | None, float | None]:
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    f1 = (
        (2 * precision * recall / (precision + recall))
        if precision is not None and recall is not None and (precision + recall) > 0
        else None
    )
    return (
        round(precision, 4) if precision is not None else None,
        round(recall, 4) if recall is not None else None,
        round(f1, 4) if f1 is not None else None,
    )


def cohen_kappa(labels: list[str], predictions: list[str]) -> float:
    """Cohen's kappa for rater agreement on a labelled multi-class set."""
    if not labels:
        return 0.0
    classes = sorted(set(labels) | set(predictions))
    n = len(labels)
    cm = confusion_matrix(labels, predictions, classes)
    po = sum(cm.matrix[i][i] for i in range(len(classes))) / n
    row = cm.row_sums
    col = [sum(cm.matrix[r][i] for r in range(len(classes))) for i in range(len(classes))]
    pe = sum((row[i] * col[i]) for i in range(len(classes))) / (n * n)
    if pe == 1.0:
        return 1.0
    return round((po - pe) / (1.0 - pe), 4) if pe != 1.0 else 0.0