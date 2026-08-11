"""Golden water-leak scenario: the complete evidence trail (Phase 11/12).

Runs the golden scenario (three reports of the same water leak near a
school, then the repair) through the FINAL ML pipeline and saves the FULL
evidence trail: vision outputs, embeddings, duplicate scores, cluster
result, severity + priority with factor evidence, and the before/after
resolution verdict.

Explicitly NOT model-performance evidence: the golden demo validates the
composition end-to-end (every model ran, every output was produced and
saved) and shows the ML evidence chain to a judge. Metrics live in the
independent frozen test sets; the demo numbers are never presented as
accuracy numbers (`model_evidence=False`).
"""

from __future__ import annotations

import json
from datetime import datetime

from civitas_duplicates.embeddings import HashNgramEmbedder
from civitas_duplicates.contracts import ReportLike
from civitas_geo.models import ExposureContext
from civitas_ml.analyze import analyze_report
from civitas_resolution.evidence import ResolutionEvidence
from civitas_resolution.model import ResolutionModel
from civitas_risk.incident_features import (
    ConsolidatedIncident,
    IncidentVisualEvidence,
    build_incident_features,
)
from civitas_risk.priority_features import PriorityContext, build_priority_features
from civitas_risk.priority_model import PriorityModel
from civitas_risk.severity_model import SeverityModel
from civitas_vision.benchmark import make_image

from civitas_evaluation import datasets
from civitas_evaluation.contracts import GoldenScenario, GoldenStep

GOLDEN_LAT = 28.6139
GOLDEN_LNG = 77.2090


def _exposure() -> ExposureContext:
    return ExposureContext(
        nearest_school_m=120.0,
        nearest_hospital_m=None,
        junction_density_1km=12.0,
        traffic_exposure="moderate",
        sources=["landmark index: Sunrise Public School at ~120 m", "map reasoning: junction density 12.0/km2"],
        inference=["moderate traffic"],
    )


def run() -> GoldenScenario:
    steps: list[GoldenStep] = []
    descriptions = [
        "water is leaking from the pipeline near sunrise school, water flowing across the road",
        "pipe burst outside the school gate, the road is flooded with running water",
        "same water leak by the school, water still flowing on the footpath",
    ]
    at = ["2026-03-01T09:00:00+00:00", "2026-03-01T11:30:00+00:00", "2026-03-01T14:00:00+00:00"]

    memory: list[ReportLike] = []
    for i in range(3):
        report_id = f"G-0{i + 1}"
        image = make_image("water_leakage", 5001 + i, "flow")
        analysis = analyze_report(
            image=image,
            description=descriptions[i],
            latitude=GOLDEN_LAT + i * 0.0002,
            longitude=GOLDEN_LNG,
            timestamp=datetime.fromisoformat(at[i]),
            report_id=report_id,
            memory_incidents=[m for m in memory],
        )
        steps.append(
            GoldenStep(
                step=f"report-{report_id}",
                payload={
                    "description": descriptions[i],
                    "media": f"procedural water-leak scene (flow variant), golden seed {5001 + i}",
                    "memory": [r.report_id for r in memory],
                },
                output={
                    "vision": analysis.vision.model_dump(),
                    "embeddings": analysis.embeddings.model_dump(),
                    "duplicate": analysis.duplicate.model_dump(),
                    "cluster": analysis.cluster.model_dump(),
                    "geospatial": analysis.geospatial.model_dump(),
                    "severity": analysis.severity.model_dump(),
                    "priority": analysis.priority.model_dump(),
                },
            )
        )
        memory.append(
            ReportLike(
                report_id=report_id,
                description=descriptions[i],
                latitude=GOLDEN_LAT + i * 0.0002,
                longitude=GOLDEN_LNG,
                submitted_at=datetime.fromisoformat(at[i]),
                category="water_leakage",
                text_embedding=HashNgramEmbedder().embed(descriptions[i]),
            )
        )

    visual = IncidentVisualEvidence(
        primary_category="water_leakage",
        observable_evidence=["water flowing across road", "standing water"],
        active_water_flow=1,
        water_coverage=0.42,
    )
    incident = ConsolidatedIncident(
        incident_id="CL-001",
        category="water_leakage",
        visual=visual,
        exposure=_exposure(),
        report_count=3,
        duration_hours=5.0,
        rain_intensity_mm_h=None,
    )
    severity = SeverityModel().assess(build_incident_features(incident))
    priority_features = build_priority_features(
        PriorityContext(incident=incident, severity_score=severity.score)
    )
    priority = PriorityModel().assess(priority_features)
    steps.append(
        GoldenStep(
            step="consolidated-severity-priority",
            payload={"incident": incident.model_dump()},
            output={
                "severity": severity.model_dump(),
                "priority": priority.model_dump(),
                "priority_signals": priority_features.model_dump(),
            },
        )
    )

    before_image = make_image("water_leakage", 5001, "flow")
    after_image = make_image("water_leakage", 5101, "dry")
    from civitas_vision.detector import VisualIntelligencePipeline

    pipeline = VisualIntelligencePipeline()
    before_vision = pipeline.analyze_image(before_image)
    after_vision = pipeline.analyze_image(after_image)
    before_evidence = ResolutionEvidence.from_vision(
        "CL-001", "before", "citizen upload (golden scenario)", before_vision, water_coverage=0.42
    )
    after_evidence = ResolutionEvidence.from_vision(
        "CL-001", "after", "inspector upload (golden scenario)", after_vision, water_coverage=0.02
    )
    resolution = ResolutionModel().assess(before_evidence, after_evidence)
    steps.append(
        GoldenStep(
            step="before-after-resolution",
            payload={
                "before_media": "procedural water-leak (flow) golden seed 5001",
                "after_media": "procedural repaired-road (dry) golden seed 5101",
            },
            output={
                "before_vision": before_vision.as_json(),
                "after_vision": after_vision.as_json(),
                "before_evidence": before_evidence.model_dump(),
                "after_evidence": after_evidence.model_dump(),
                "resolution": resolution.model_dump(),
            },
        )
    )

    scenario = GoldenScenario(
        scenario_id="golden-water-leak",
        steps=steps,
        model_evidence=False,
    )
    (datasets.RESULTS_DIR / "golden").mkdir(parents=True, exist_ok=True)
    (datasets.RESULTS_DIR / "golden" / "evidence_trail.json").write_text(
        json.dumps(json.loads(scenario.model_dump_json()), indent=2), encoding="utf-8"
    )
    return scenario