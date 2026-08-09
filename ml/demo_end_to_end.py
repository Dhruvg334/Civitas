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
for rel in ("ml/duplicates/src", "ml/risk/src", "geospatial/src"):
    sys.path.insert(0, str(REPO / rel))

from civitas_duplicates import DuplicateDetector, ReportLike  # noqa: E402
from civitas_geo.feature_engineering import (
    CivicIncidentContext,
    GeospatialFeatureEngine,
)
from civitas_geo.landmarks import LandmarkIndex  # noqa: E402
from civitas_geo.models import GeoPoint, SpatialSearchSpec  # noqa: E402
from civitas_geo.reasoning import compute_exposure  # noqa: E402
from civitas_geo.retrieval import NearbyRetriever  # noqa: E402
from civitas_risk import RiskAssessor, RiskContext, SeverityAssessor  # noqa: E402

T0 = datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)


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


if __name__ == "__main__":
    main()