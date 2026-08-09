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
for rel in ("ml/duplicates/src", "ml/risk/src", "ml/vision/src", "ml/resolution/src", "services/ml/src", "geospatial/src"):
    sys.path.insert(0, str(REPO / rel))

try:  # Phase 5 reasons use the "✓" check mark; force UTF-8 on cp1252 consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001 - stdout may not be reconfigurable everywhere
    pass

from civitas_duplicates import (  # noqa: E402
    ClassicalImageEmbedder,
    DuplicateDetector,
    HashNgramEmbedder,
    ReportLike,
    build_report_embeddings,
    evaluate_engine,
    incident_similarity,
)
from civitas_duplicates.benchmark import make_synthetic_pairs  # noqa: E402
from civitas_duplicates.evaluation import build_labelled_pairs  # noqa: E402
from civitas_ml import analyze_report, verify_resolution  # noqa: E402
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
from civitas_resolution import (  # noqa: E402
    ResolutionEvidence,
    ResolutionModel,
    outcome_label,
)
from civitas_risk import (  # noqa: E402
    ConsolidatedIncident,
    IncidentVisualEvidence,
    PriorityContext,
    PriorityModel,
    RiskAssessor,
    RiskContext,
    SeverityAssessor,
    SeverityModel,
    build_incident_features,
    build_priority_features,
)
from civitas_vision.benchmark import gaussian_blur, make_image  # noqa: E402
from civitas_vision.detector import VisualIntelligencePipeline  # noqa: E402
from civitas_vision.features import extract_features  # noqa: E402

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

    print("\n== 9. Duplicate detection engine (Phase 5) ==")
    print("  Three citizen reports arrive within 75 minutes around the same spot")
    print("  (~34 m apart, near Sunrise School): R1 water leak 10:30, "
          "R2 flooding 11:00, R3 road damage 11:45.")
    day = T0 + timedelta(hours=2, minutes=30)  # 10:30 AM
    spot: list[tuple[float, float]] = [
        (28.6139, 77.2090), (28.6140, 77.2091), (28.6142, 77.2092),
    ]
    scene_water = "water_leakage"
    engine_reports: list[ReportLike] = []
    engine_density_records: list[dict[str, object]] = []
    for i, (desc, cat, delta_min, seed) in enumerate(
        [
            ("water leaking from the main pipe near sunrise school gate, road is wet",
             "water leak", 0, 7101),
            ("flooding on the road in front of sunrise school, water across the footpath",
             "flooding", 30, 7102),
            ("road surface breaking up after the water, deep cracks near the school",
             "road damage", 75, 7103),
        ]
    ):
        lat, lon = spot[i]
        scene = make_image(scene_water if i < 2 else "pothole_road_damage", seed)
        engine_reports.append(
            ReportLike(
                report_id=f"R{i + 1}",
                description=desc,
                latitude=lat, longitude=lon,
                submitted_at=day + timedelta(minutes=delta_min),
                category=cat,
                landmark_ids=["lm-school-01", "lm-junction-01"],
                image_embedding=image_embedder.embed_image(scene).vector,
                media_count=1,
            )
        )
        engine_density_records.append(
            {"incident_id": f"R{i + 1}", "latitude": lat, "longitude": lon,
             "category": cat, "duplicates_seen": 1, "reported_at": day + timedelta(minutes=delta_min)}
        )
    print("  1) candidate retrieval (800 m / 24 h window, memory mode)")
    engine_candidates = candidate_retriever.retrieve(
        CandidateSearchSpec(
            center=GeoPoint(latitude=spot[0][0], longitude=spot[0][1]),
            radius_m=800, within_hours=24, limit=10,
        ),
        memory_incidents=engine_density_records,
        landmarks=landmarks,
        now=day + timedelta(minutes=90),
    )
    print(f"     candidates for R1 in window: "
          f"{[c.incident_id for c in engine_candidates.candidates]}")
    print("  2) pairwise features -> duplicate score with explainable reasons")
    engine = DuplicateDetector(
        landmark_index=landmarks,
        density_records=engine_density_records,
        cluster_id_start=18,
    )
    for i in range(3):
        for j in range(i + 1, 3):
            pair_result = engine.evaluate_pair(engine_reports[i], engine_reports[j])
            print(f"     {engine_reports[i].report_id} vs {engine_reports[j].report_id}: "
                  f"score {pair_result.score:.2f} duplicate={pair_result.is_duplicate}")
            for reason in pair_result.reasons:
                print(f"        {reason}")
    print("  3) incident clustering stage")
    engine_clusters = engine.cluster(engine_reports)
    for cluster in engine_clusters:
        print(f"     {' ─┐' if cluster.member_count > 1 else '     '} "
              f"{cluster.summarizing_note} (ID {cluster.cluster_id})")
    main_cluster = next(c for c in engine_clusters if c.member_count > 1)
    print(f"     -> merged {main_cluster.report_ids} into incident {main_cluster.cluster_id}")
    print("  4) labelled evaluation: positive / negative / ambiguous pairs")
    labelled = build_labelled_pairs(seed=11, n_per_label=6, with_images=True)
    labelled_ev = evaluate_engine(labelled, engine=engine)
    for row in labelled_ev.rows:
        verdict = "merge" if row.is_duplicate else ("review" if row.requires_review else "reject")
        print(f"     [{row.label:9s}] score {row.score:.2f} -> {verdict:6s} | {row.note}")
    print(f"  {labelled_ev.summary()}")

    print("\n== 10. Consolidated incident severity (Phase 6) ==")
    print("  Question: how bad is the merged incident CL-018?")
    print("  Visual evidence (from the CV pipeline on R1's photo) + geospatial")
    print("  intelligence (landmark index around the spot) + context.")
    r1_scene = make_image("water_leakage", 7101)
    r1_visual = vision.analyze_image(r1_scene)
    incident_visual = IncidentVisualEvidence.from_evidence(
        primary_category=r1_visual.primary_category,
        observed_evidence=list(r1_visual.observable_evidence),
        water_coverage=extract_features(r1_scene)["blue_smooth_share"],
    )
    incident_point = GeoPoint(latitude=engine_reports[0].latitude,
                              longitude=engine_reports[0].longitude)
    incident_nearby = NearbyRetriever(executor=None).retrieve(
        SpatialSearchSpec(center=incident_point, radius_m=800, limit=10),
        memory_incidents=engine_density_records,
    )
    incident_exposure = compute_exposure(
        incident_point, landmarks=landmarks, nearby=incident_nearby
    )
    incident = ConsolidatedIncident(
        incident_id=main_cluster.cluster_id,
        category="water leak",
        visual=incident_visual,
        exposure=incident_exposure,
        report_count=main_cluster.member_count,
        duration_hours=(
            (engine_reports[-1].submitted_at - engine_reports[0].submitted_at)
            .total_seconds() / 3600.0
        ),
    )
    incident_features6 = build_incident_features(incident)
    print("  engineered severity features (evidence only):")
    feature_lines = [
        ("active_water_flow", lambda v: f"active_water_flow = {v}"),
        ("water_coverage", lambda v: f"water_coverage = {v:.2f} (flooded-area share)"),
        ("school_distance_m", lambda v: f"school_distance = {v:.0f} m"),
        ("hospital_distance_m", lambda v: f"hospital_distance = {v:.0f} m"),
        ("traffic_exposure", lambda v: f"traffic_exposure = {v}"),
        ("report_count", lambda v: f"report_count = {v}"),
        ("duration_hours", lambda v: f"duration = {v:.1f} h"),
    ]
    for key, fmt in feature_lines:
        value = getattr(incident_features6, key)
        print(f"    {fmt(value) if value is not None else f'{key} = <absent> (recorded, not guessed)'}")
    print("  SeverityModel (one incident -> how bad?):")
    severity6 = SeverityModel().assess(incident_features6)
    print(f"    Severity score: {severity6.score}")
    print(f"    Severity level: {severity6.level.upper()}")
    print("    Contributing factors:")
    for c in severity6.contributing_factors:
        print(f"      - {c.factor} (+{c.points} pts; {c.evidence})")
    print("  PriorityModel (separate decision -> how urgent?):")
    incident_geo = GeospatialFeatureEngine(landmarks=landmarks).compute(
        CivicIncidentContext(
            latitude=engine_reports[0].latitude,
            longitude=engine_reports[0].longitude,
            submitted_at=engine_reports[0].submitted_at,
            category=engine_reports[0].category,
            nearby_reports=incident_nearby.incidents,
        )
    )
    priority7_context = PriorityContext(
        incident=incident,
        severity_score=severity6.score,
        population_density_proxy=incident_geo.features["population_density_proxy"],
        nearby_density_norm=incident_geo.features["incident_density_1km"],
        current_time=day + timedelta(minutes=90),  # 12:00 scenario clock
    )
    priority_features7 = build_priority_features(priority7_context)
    priority7 = PriorityModel().assess(priority_features7)
    print(f"    Priority score: {priority7.score}")
    print(f"    Priority level: {priority7.level.upper()}")
    print("    Reasons (each cites the evidence it saw):")
    for r in priority7.reasons:
        print(f"      - {r.factor} (+{r.points} pts; {r.evidence})")

    print("\n== 11. Priority feature engineering (Phase 7) ==")
    print("  Question: how urgently must the municipality respond to CL-018?")
    print("  Ten signals drive a model separate from severity, so urgency stays")
    print("  independent of danger. Engineered feature vector (evidence only):")
    table = [
        ("severity_score", priority_features7.severity_score, "severity verdict (one-way input)"),
        ("school_proximity", priority_features7.school_proximity, "school at 0 m - children in the street"),
        ("hospital_proximity", priority_features7.hospital_proximity, "hospital 584 m away"),
        ("traffic_exposure", priority_features7.traffic_exposure, "moderate"),
        ("population_exposure", priority_features7.population_exposure, "sparse block (proxy)"),
        ("repeated_reports", priority_features7.repeated_reports, "3 independent reports corroborate"),
        ("incident_duration", priority_features7.incident_duration, "1.25 h old"),
        ("nearby_density", priority_features7.nearby_density, "grid-cell density norm, quiet neighbourhood"),
        ("category_urgency", priority_features7.category_urgency, "water leak = flooding risk"),
        ("time_sensitivity", priority_features7.time_sensitivity, "noon = school hours, worst time to flood"),
    ]
    for name, value, basis in table:
        print(f"    {name:22s} = {value:.2f}   ({basis})")
    print("  PriorityModel -> how urgent:")
    print(f"    Priority score: {priority7.score}")
    print(f"    Priority level: {priority7.level.upper()}")
    for r in priority7.reasons:
        print(f"      - {r.factor} (+{r.points} pts; {r.evidence})")
    print("  Sensitivity walk (hypothetical what-ifs - labelled, never applied")
    print("  to the observed incident; the walk shows where CRITICAL comes from):")
    walk_rows = [
        ("A", "same leak at a heavy-traffic junction, 6 reports, rain, 3 h old", dict(
            severity_score=80, school_proximity=1.0, hospital_proximity=1.0,
            traffic_exposure=1.0, population_exposure=0.5, repeated_reports=0.92,
            incident_duration=0.12, nearby_density=0.4, category_urgency=0.6,
            time_sensitivity=1.0)),
        ("B", "multi-day worst case: 9 reports, 96 h old, dense cell, severity critical", dict(
            severity_score=80, school_proximity=1.0, hospital_proximity=1.0,
            traffic_exposure=1.0, population_exposure=0.85, repeated_reports=0.98,
            incident_duration=1.0, nearby_density=0.9, category_urgency=0.6,
            time_sensitivity=1.0)),
    ]
    for label, story, signals in walk_rows:
        walked = PriorityModel().assess(priority_features7.model_copy(
            update={k: v for k, v in signals.items()}
        ))
        print(f"    what-if {label}: {story}")
        print(f"      -> Priority score: {walked.score} | level {walked.level.upper()}")
    print("  (>80 CRITICAL always goes to a human reviewer; the score is the sum")
    print("   of ten weighted signals, each shown with its evidence.)")

    print("\n== 12. Resolution verification (Phase 8) ==")
    print("  Question: did the municipality actually fix CL-018?")
    print("  The work order was dispatched after the priority verdict and the")
    print("  field team closed it as 'resolved'. This is the second ML moment:")
    print("  the vision pipeline re-analyzes the AFTER photo and the model")
    print("  compares its evidence with the BEFORE photo (R1's upload).")
    before_photo = make_image("water_leakage", 7101, variant="flow")
    verification_before = ResolutionEvidence.from_vision(
        main_cluster.cluster_id, "before", "citizen upload (R1, at report time)",
        vision.analyze_image(before_photo),
        water_coverage=extract_features(before_photo)["blue_smooth_share"],
    )
    after_photo = make_image("water_leakage", 7101, variant="default")
    verification_after = ResolutionEvidence.from_vision(
        main_cluster.cluster_id, "after", "inspector upload (2 weeks later)",
        vision.analyze_image(after_photo),
        water_coverage=extract_features(after_photo)["blue_smooth_share"],
    )
    print(f"  BEFORE evidence: {sorted(verification_before.observable_evidence)}")
    print(f"  AFTER evidence : {sorted(verification_after.observable_evidence)}")
    resolution_model = ResolutionModel()
    verdict8 = resolution_model.assess(verification_before, verification_after)
    print(f"  ResolutionModel -> {outcome_label(verdict8.outcome)}")
    for r in verdict8.reasons:
        print(f"    - {r.factor}: {r.status} ({r.evidence})")
    print("  The road is no longer flooded but puddles remain — the work order")
    print("  is NOT closed; it goes back to the field team for follow-up.")
    print("  Re-checks (same model, other before/after pairs):")
    dry_photo = make_image("water_leakage", 7101, variant="dry")
    dry_after = ResolutionEvidence.from_vision(
        main_cluster.cluster_id, "after", "inspector upload (dry road)",
        vision.analyze_image(dry_photo),
        water_coverage=extract_features(dry_photo)["blue_smooth_share"],
    )
    dry_verdict = resolution_model.assess(verification_before, dry_after)
    print(f"    dry road after:    -> {outcome_label(dry_verdict.outcome)} (all signals gone, confidence {dry_verdict.confidence:.2f})")
    fresh_after = ResolutionEvidence.from_vision(
        main_cluster.cluster_id, "after", "inspector upload (leak restarting)",
        vision.analyze_image(make_image("water_leakage", 7101, variant="flow")),
        water_coverage=extract_features(make_image("water_leakage", 7101, variant="flow"))["blue_smooth_share"],
    )
    print(f"    leak restarting:   -> {outcome_label(resolution_model.assess(verification_before, fresh_after).outcome)} (flow still observable)")
    blurry_after = ResolutionEvidence.from_vision(
        main_cluster.cluster_id, "after", "inspector upload (blurry)",
        vision.analyze_image(gaussian_blur(after_photo, radius=4)),
        water_coverage=extract_features(gaussian_blur(after_photo, radius=4))["blue_smooth_share"],
    )
    print(f"    blurry after photo -> {outcome_label(resolution_model.assess(verification_before, blurry_after).outcome)} (quality gate rejects media)")

    print("\n== 13. One ML service (Phase 9) ==")
    print("  The pieces above are now exposed behind ONE stable ML interface")
    print("  with typed, schema-validated outputs for the LangGraph agents:")
    print("      analyze_report(image, video, description, lat, lng, timestamp)")
    print("      verify_resolution(before_media, after_media)")
    print("  analyze_report on the same R1 photo + text + location stack:")
    service_analysis = analyze_report(
        image=before_photo,
        video=None,
        description="waterlogging near school again, road flooding",
        latitude=28.6139,
        longitude=77.2090,
        timestamp=T0 + timedelta(hours=4),
        memory_incidents=engine_reports[1:],
        landmarks=LandmarkIndex(),
    )
    print(f"    vision    -> {service_analysis.vision.primary_category}, media_usable={service_analysis.vision.media_usable}")
    best = service_analysis.duplicate.best_match
    print(f"    duplicate -> verdict={service_analysis.duplicate.verdict}, best match={best.report_id}"
          f" (similarity {best.similarity:.2f}, {best.reasons[0]})")
    print(f"    severity  -> score {service_analysis.severity.score:.2f} ({service_analysis.severity.level}) "
          f"[top: {service_analysis.severity.factors[0].factor}]")
    print(f"    priority  -> score {service_analysis.priority.score:.2f} ({service_analysis.priority.level}) "
          f"[top: {service_analysis.priority.reasons[0].factor}] / single-report view: clustering adds the rest")
    print("  verify_resolution on the same BEFORE/AFTER pair:")
    service_verdict = verify_resolution(before_photo, after_photo)
    print(f"    {{'status': '{service_verdict.status}', 'confidence': {service_verdict.confidence:.2f}, 'evidence': {service_verdict.evidence[:2]}}}")
    dry_verdict = verify_resolution(before_photo, dry_photo)
    print(f"    {{'status': '{dry_verdict.status}', 'confidence': {dry_verdict.confidence:.2f}, 'evidence': {dry_verdict.evidence[:2]}}} "
          "(dry road after)")
    print("  Note: severity/priority here are single-report (no cluster bonus);")
    print("  the cluster-aware numbers live in the risk layer the service composes.")


if __name__ == "__main__":
    main()