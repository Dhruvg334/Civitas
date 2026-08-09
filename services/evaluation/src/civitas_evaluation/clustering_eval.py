"""Incident-clustering evaluation (Phase 11/12).

Verifies that multiple reports of the same real-world incident consolidate
into one cluster while separate nearby incidents remain separate. Four
scenarios: one incident (3 reports), two nearby incidents (2+2), a
confusable same-text pair at two locations, and same-location
different-category pairs. Every scenario records the actual clusters with
their edges so successful and failed cases are both inspectable.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from civitas_duplicates.detector import DuplicateDetector
from civitas_duplicates.embeddings import HashNgramEmbedder
from civitas_duplicates.contracts import ReportLike

from civitas_evaluation import datasets
from civitas_evaluation.contracts import ComponentMetrics

COMPONENT = "incident-clustering"


def _as_report_like(raw: dict[str, Any]) -> ReportLike:
    return ReportLike(
        report_id=str(raw["report_id"]),
        description=str(raw["description"]),
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
        submitted_at=datetime.fromisoformat(str(raw["submitted_at"])),
        category=str(raw["category"]),
        text_embedding=HashNgramEmbedder().embed(str(raw["description"])),
    )


def _expected_map(scenario: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for cluster in scenario["expected_clusters"]:
        for rid in cluster["report_ids"]:
            out[str(rid)] = str(cluster["incident"])
    return out


def run() -> tuple[ComponentMetrics, list[dict[str, Any]]]:
    scenarios = datasets.load_labels("clusters/labels.json")
    engine = DuplicateDetector()
    rows: list[dict[str, Any]] = []
    correct_scenarios = 0
    for scenario_raw in scenarios:
        scenario: dict[str, Any] = dict(scenario_raw)
        reports = [_as_report_like(r) for r in scenario["reports"]]
        clusters = engine.cluster(reports)
        actual: dict[str, str] = {}
        for cluster in clusters:
            for rid in cluster.report_ids:
                actual[rid] = cluster.cluster_id
        expected = _expected_map(scenario)

        merged_correctly = all(actual[a] == actual[b] for a, b in _pairs_of(expected) if expected[a] == expected[b])
        separated_correctly = all(actual[a] != actual[b] for a, b in _pairs_of(expected) if expected[a] != expected[b])
        ok = merged_correctly and separated_correctly
        correct_scenarios += int(ok)

        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "expected_incidents": expected,
                "actual_clusters": actual,
                "cluster_details": [
                    {"cluster_id": c.cluster_id, "report_ids": c.report_ids, "span_m": c.span_m}
                    for c in clusters
                ],
                "merged_correctly": merged_correctly,
                "separated_correctly": separated_correctly,
                "correct": ok,
            }
        )

    metrics = ComponentMetrics(
        component=COMPONENT,
        model_version="duplicates-engine-v1 (clustering stage)",
        thresholds={"duplicate_threshold": "0.70 (edge criterion, frozen)"},
        test_set="test_data/clusters (4 scenarios, 16 labelled reports)",
        n=len(scenarios),
        metrics={
            "scenarios_fully_correct": correct_scenarios,
            "scenario_accuracy": round(correct_scenarios / len(scenarios), 4),
            "same_incident_pairs_merged": sum(
                1
                for r in rows
                for a, b in _pairs_of(r["expected_incidents"])
                if r["expected_incidents"][a] == r["expected_incidents"][b]
                and r["actual_clusters"][a] == r["actual_clusters"][b]
            ),
            "different_incident_pairs_separated": sum(
                1
                for r in rows
                for a, b in _pairs_of(r["expected_incidents"])
                if r["expected_incidents"][a] != r["expected_incidents"][b]
                and r["actual_clusters"][a] != r["actual_clusters"][b]
            ),
        },
        notes=[
            "report-level pair accuracy separates 'merges that must happen' from 'merges that must not happen'",
        ],
    )
    (datasets.RESULTS_DIR / "clustering_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    (datasets.RESULTS_DIR / "clustering_metrics.json").write_text(
        json.dumps(json.loads(metrics.model_dump_json()), indent=2), encoding="utf-8"
    )
    return metrics, rows


def _pairs_of(mapping: dict[str, str]) -> list[tuple[str, str]]:
    ids = sorted(mapping)
    return [(ids[i], ids[j]) for i in range(len(ids)) for j in range(i + 1, len(ids))]