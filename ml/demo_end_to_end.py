"""End-to-end Civitas intelligence demo: reports -> duplicates -> geospatial
exposure -> severity and priority.

Runs entirely offline (memory retrieval + demo landmarks) and prints the full
decision trace for one scenario: three citizens report a water leak near a
school.

Usage:
    python ml/demo_end_to_end.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
for rel in ("ml/duplicates/src", "ml/risk/src", "ml/vision/src", "geospatial/src"):
    sys.path.insert(0, str(REPO / rel))

from civitas_duplicates import (  # noqa: E402
    ClassicalImageEmbedder,
    DuplicateDetector,
    HashNgramEmbedder,
    ReportLike,
    build_report_embeddings,
    incident_similarity,
)
from civitas_duplicates.benchmark import make_synthetic_pairs  # noqa: E402
from civitas_geo.aggregates import DensityAggregator  # noqa: E402
from civitas_geo.candidates import CandidateRetriever  # noqa: E402
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
)
from civitas_geo.landmarks import LandmarkIndex  # noqa: E402
from civitas_geo.models import (  # noqa: E402
    CandidateSearchSpec,
    GeoPoint,
    SpatialSearchSpec,
)
from civitas_geo.reasoning import compute_exposure  # noqa: E402
from civitas_geo.retrieval import NearbyRetriever  # noqa: E402
from civitas_geo.validation import gate_for_pipeline  # noqa: E402
from civitas_risk import RiskAssessor, RiskContext, SeverityAssessor  # noqa: E402
from civitas_vision.benchmark import gaussian_blur, make_image  # noqa: E402
from civitas_vision.detector import VisualIntelligencePipeline  # noqa: E402

T0 = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)


def run_benchmark_evaluation():
    from civitas_vision.benchmark import run_evaluation

    return run_evaluation()


def main() -> None:
    landmarks = LandmarkIndex()
    detector = DuplicateDetector(landmark_index=landmarks)
    risks = RiskAssessor(severity=SeverityAssessor())

    reports = [
        ReportLike(
            report_id="rep-1",
            description="water leaking on the road near sunrise school, two wheelers slipping",
            latitude=28.6139, longitude=77.2090,
            submitted_at=T0,
            category="water leak",
        ),
        ReportLike(
            report_id="rep-2",
            description="pipe burst causing flooding near the school gate",
            latitude=28.6141, longitude=77.2093,
            submitted_at=T0 + timedelta(hours=2),
            category="water leakage",
        ),
        ReportLike(
            report_id="rep-3",
            description="streetlight dark near the civic centre metro",
            latitude=28.6190, longitude=77.2165,
            submitted_at=T0 + timedelta(hours=6),
            category="streetlight",
        ),
    ]

    print("== 1. Duplicate detection ==")
    clusters = detector.cluster(reports)
    for cl in clusters:
        print(f"  {cl.summarizing_note}")

    merged = next(cl for cl in clusters if cl.member_count > 1)
    rep = next(r for r in reports if r.report_id == merged.representative_report_id)
    rep_ids = merged.report_ids
    print(f"  -> merged cluster: {rep_ids}, representative {merged.representative_report_id}")

    print("\n== 2. Geospatial intelligence ==")
    retriever = NearbyRetriever(executor=None)  # offline memory mode
    point = GeoPoint(latitude=rep.latitude, longitude=rep.longitude)
    nearby = retriever.retrieve(
        SpatialSearchSpec(center=point, radius_m=800, limit=10),
        memory_incidents=[
            {"incident_id": i, "latitude": r.latitude, "longitude": r.longitude,
             "category": r.category, "duplicates_seen": 1}
            for i, r in enumerate(reports)
        ],
    )
    print(f"  nearby incidents in 800 m: {[n.incident_id for n in nearby.incidents]} ({nearby.mode})")
    exposure = compute_exposure(point, landmarks=landmarks, nearby=nearby)
    print(f"  exposure: school {exposure.nearest_school_m}m away, "
          f"hospital {exposure.nearest_hospital_m}m, traffic {exposure.traffic_exposure}, "
          f"junctions {exposure.junction_density_1km}/km2")

    print("\n== 2b. Geospatial feature vector (evidence, no decisions) ==")
    geo_features = GeospatialFeatureEngine(landmarks=landmarks).compute(
        CivicIncidentContext(
            latitude=rep.latitude, longitude=rep.longitude,
            submitted_at=rep.submitted_at, category=rep.category,
            nearby_reports=nearby.incidents,
        )
    )
    for name in (
        "location_validity", "school_proximity", "hospital_proximity", "traffic",
        "population_density_proxy", "nearby_report_count", "incident_density_1km",
        "nearest_report_distance_sim", "repeated_reports", "time_since_first_report_norm",
    ):
        print(f"    {name:32s} = {geo_features.features[name]:.3f}  ({geo_features.provenance[name][:64]})")

    print("\n== 2c. Candidate list for the ML duplicate engine ==")
    gate = gate_for_pipeline({"latitude": rep.latitude, "longitude": rep.longitude})
    print(f"  gate: can_enter={gate.can_enter} reason={gate.reason} "
          f"(rejected reports go to the fix queue, not the spatial pipeline)")
    candidate_retriever = CandidateRetriever(executor=None)  # offline memory mode
    candidates = candidate_retriever.retrieve(
        CandidateSearchSpec(
            center=point, radius_m=800, within_hours=24, limit=10,
            exclude_incident_ids=[f"inc-{reports.index(rep)}"],
        ),
        memory_incidents=[
            {"incident_id": f"inc-{i}", "latitude": r.latitude, "longitude": r.longitude,
             "category": r.category, "duplicates_seen": 1,
             "reported_at": r.submitted_at}
            for i, r in enumerate(reports)
        ],
        landmarks=landmarks,
        now=T0 + timedelta(hours=6),  # scenario-relative clock; PostGIS uses now()
    )
    for cand in candidates.candidates:
        near_landmarks = ", ".join(
            f"{d.landmark.kind}:{d.landmark.landmark_id}@{d.distance_m:.0f}m"
            for d in cand.landmark_context[:3]
        )
        print(f"  candidate {cand.incident_id}: {cand.distance_m:.0f}m away, "
              f"reported {cand.hours_since_reported:.1f}h ago, cat='{cand.category}', "
              f"dups={cand.duplicates_seen}, landmarks=[{near_landmarks}]")
    print(f"  ({candidates.mode}, boundary: {candidates.boundary.description if candidates.boundary else 'none'})")

    print("\n== 3. Severity and priority ==")
    context = RiskContext(
        report_id=merged.cluster_id,
        category=rep.category or "water_leak",
        description=rep.description,
        exposure=exposure,
        repeated_reports=merged.member_count,
        open_hours=6.0,
        rain_intensity_mm_h=25.0,
    )
    assessment = risks.assess(context)
    print(f"  {assessment.summary()}")
    print("  severity basis:")
    for line in assessment.severity.decision_basis[:4]:
        print(f"    - {line}")
    print("  priority basis:")
    for line in assessment.priority.decision_basis[:3]:
        print(f"    - {line}")

    print("\n== 4. Pair trace (explainable duplicate decision) ==")
    pair = detector.evaluate_pair(rep, next(r for r in reports if r.report_id != rep.report_id and r.report_id in rep_ids))
    print(f"  score {pair.score:.2f} duplicate={pair.is_duplicate} review={pair.requires_review}")
    for line in pair.decision_basis:
        print(f"    - {line}")

    print("\n== 5. Computer vision (image and video media) ==")
    vision = VisualIntelligencePipeline()
    water_image = make_image("water_leakage", 7000, "flow")
    water_result = vision.analyze_image(water_image)
    print(f"  image -> {water_result.as_json()}")
    for line in water_result.basis[:3]:
        print(f"    - {line}")
    video_sharp = make_image("broken_streetlight", 7001)
    video_result = vision.analyze_video(
        "media/video.mp4",
        video_extra_frames=[video_sharp, gaussian_blur(video_sharp, 5.0)],
    )
    print(f"  video -> {video_result.as_json()} (frames selected {video_result.frames_selected})")
    blur_gate = vision.analyze_image(gaussian_blur(water_image, 5.0))
    print(f"  blurred media usable={blur_gate.media_usable}: {blur_gate.quality.reasons[0] if blur_gate.quality else ''}")

    print("\n== 6. Benchmark evaluation (measurable CV performance) ==")
    evaluation = run_benchmark_evaluation()
    print(f"  accuracy {evaluation.accuracy:.3f} | macro-F1 {evaluation.macro_f1:.3f} "
          f"| {evaluation.n_samples} held-out images")
    for cat, m in evaluation.per_class.items():
        print(f"    {cat:22s} precision {m['precision']:.2f} recall {m['recall']:.2f} f1 {m['f1']:.2f}")

    print("\n== 7. Embeddings + same-incident similarity (Phase 4) ==")
    text_embedder = HashNgramEmbedder()
    image_embedder = ClassicalImageEmbedder()

    emb_a = build_report_embeddings(
        report_id="rep-1",
        description=reports[0].description,
        text_embedder=text_embedder,
        image=make_image("water_leakage", 7021),
        image_embedder=image_embedder,
        gps=(reports[0].latitude, reports[0].longitude),
        submitted_at=reports[0].submitted_at.isoformat(),
        category=reports[0].category,
        landmark_ids=["lm-school-1"],
    )
    emb_b = build_report_embeddings(
        report_id="rep-2",
        description=reports[1].description,
        text_embedder=text_embedder,
        image=make_image("water_leakage", 7022),
        image_embedder=image_embedder,
        gps=(reports[1].latitude, reports[1].longitude),
        submitted_at=reports[1].submitted_at.isoformat(),
        category=reports[1].category,
        landmark_ids=["lm-school-1"],
    )
    emb_c = build_report_embeddings(
        report_id="rep-3",
        description=reports[2].description,
        text_embedder=text_embedder,
        image=make_image("broken_streetlight", 7023),
        image_embedder=image_embedder,
        gps=(reports[2].latitude, reports[2].longitude),
        submitted_at=reports[2].submitted_at.isoformat(),
        category=reports[2].category,
        landmark_ids=["lm-metro-station-1"],
    )
    print(f"  image embedding: {image_embedder.method} "
          f"(dim {len(emb_a.image_embedding or [])})")
    answer = incident_similarity(emb_a, emb_b)
    print(f"  rep-1 vs rep-2 (same leak) -> duplicate={answer.is_duplicate} "
          f"score={answer.score:.2f} review={answer.requires_review}")
    for line in answer.decision_basis[:3]:
        print(f"    - {line}")
    answer_far = incident_similarity(emb_a, emb_c)
    print(f"  rep-1 vs rep-3 (different incident) -> duplicate={answer_far.is_duplicate} "
          f"score={answer_far.score:.2f}")
    for line in answer_far.decision_basis[:2]:
        print(f"    - {line}")
    synthetic_pairs = make_synthetic_pairs(seed=7, n_duplicates=10, n_distinct=10)
    agree = sum(
        int(incident_similarity(a, b).is_duplicate) == label
        for a, b, label in synthetic_pairs
    )
    print(f"  synthetic pair check: {agree}/20 same-incident answers correct")

    print("\n== 8. Reports-per-cell density aggregates (Phase 4) ==")
    memory_incidents = [
        {"incident_id": f"inc-{i}", "latitude": r.latitude, "longitude": r.longitude,
         "category": r.category, "duplicates_seen": 1, "reported_at": r.submitted_at}
        for i, r in enumerate(reports)
    ]
    density = DensityAggregator(cell_size_m=200).reports_per_cell(memory_incidents)
    print(f"  density: {density.cell_count()} non-empty 200 m cells "
          f"over {density.total_reports} report(s) ({density.mode})")
    for cell in density.top_cells(3):
        print(f"    cell {cell.cell_id}: {cell.report_count} report(s), "
              f"categories {cell.category_distribution}")
    grid_features = GeospatialFeatureEngine(landmarks=landmarks).compute(
        CivicIncidentContext(
            latitude=rep.latitude, longitude=rep.longitude,
            submitted_at=rep.submitted_at, category=rep.category,
            nearby_reports=nearby.incidents,
            cell_report_density=density.cells[0].report_count if density.cells else None,
        )
    )
    print(f"  cell_report_density_norm = {grid_features.features['cell_report_density_norm']:.3f} "
          f"({grid_features.provenance['cell_report_density_norm']})")


if __name__ == "__main__":
    main()