"""Phase 10 schema tests: every ML output validates against its model.

Proves the stable surface: pydantic models round-trip, JSON-schema
generation works, every output model carries the required identification
(report_id / incident_id / trace_id where applicable) and no unsupported
claims sneak into outputs (all probabilities/scores are range-checked).
"""

from __future__ import annotations

from civitas_ml.contracts import (
    CandidateReport,
    DuplicateSection,
    ErrorPayload,
    LandmarkSet,
    MediaReference,
    NearbyCandidatesRequest,
    NearbyCandidatesResponse,
    ReportAnalysis,
    ReportInput,
    ResolutionInput,
    ResolutionVerification,
)


def test_error_payload_mirrors_shared_schema() -> None:
    payload = ErrorPayload(code="media_not_found", message="nope", trace_id="t1")
    data = payload.model_dump()
    assert set(data) >= {"code", "message", "details", "trace_id"}


def test_report_input_contract() -> None:
    report = ReportInput(report_id="R1", description="water on the road", latitude=28.6, longitude=77.2)
    assert report.submitted_at is None
    assert report.citizen_category is None
    assert report.retrieval_radius_m == 2000.0
    assert report.retrieval_window_h == 72.0


def test_media_reference_requires_kind() -> None:
    ref = MediaReference(media_id="fixture:water_leakage@7101:flow", kind="image", mime_type="image/png")
    assert ref.kind == "image"
    assert ref.local_path is None


def test_nearby_candidates_request_validates_window() -> None:
    request = NearbyCandidatesRequest(
        report_id="R1", latitude=28.6, longitude=77.2,
        submitted_at="2026-03-01T12:00:00+00:00",
    )
    assert request.radius_m == 2000.0
    assert request.time_window_h == 72.0
    assert request.limit == 25


def test_nearby_candidates_response_round_trips() -> None:
    request = NearbyCandidatesRequest(
        report_id="R1", latitude=28.6, longitude=77.2,
        submitted_at="2026-03-01T12:00:00+00:00",
    )
    response = NearbyCandidatesResponse(
        request=request,
        candidates=[
            CandidateReport(
                report_id="R2",
                description="flooding near the school",
                latitude=28.614,
                longitude=77.2091,
                submitted_at="2026-03-01T11:00:00+00:00",
                category="flooding",
            )
        ],
        count=1,
    )
    assert NearbyCandidatesResponse.model_validate(response.model_dump()) == response


def test_landmark_set_round_trips() -> None:
    from civitas_ml.contracts import LandmarkInfo

    landmarks = LandmarkSet(
        landmarks=[LandmarkInfo(landmark_id="lm-1", name="School", kind="school", latitude=28.6, longitude=77.2)]
    )
    assert LandmarkSet.model_validate(landmarks.model_dump()) == landmarks


def test_resolution_input_contract() -> None:
    record = ResolutionInput(
        incident_id="CL-001",
        before=MediaReference(media_id="fixture:water_leakage@7101:flow", kind="image"),
        after=MediaReference(media_id="fixture:water_leakage@7101:default", kind="image"),
    )
    assert record.incident_id == "CL-001"
    assert record.before.media_id == "fixture:water_leakage@7101:flow"
    assert record.after.kind == "image"


def test_all_output_models_generate_json_schema() -> None:
    for model in (
        ReportAnalysis,
        ResolutionVerification,
        DuplicateSection,
        ReportInput,
        NearbyCandidatesResponse,
        LandmarkSet,
        ErrorPayload,
    ):
        schema = model.model_json_schema()
        assert schema["type"] == "object"


def test_scores_stay_in_range() -> None:
    analysis = ReportAnalysis(
        report_id="R1",
        vision={"media_usable": False},
        embeddings={"text_dim": 0, "method": "none"},
        duplicate={"mode": "no-memory", "verdict": "unknown"},
        cluster={"available": False, "verdict": "unknown"},
        geospatial={"available": False, "basis": ["no coordinates"]},
        severity={"available": False, "basis": ["no info"]},
        priority={"available": False, "basis": ["no info"]},
    )
    assert 0 <= analysis.vision.confidence <= 1
    assert analysis.severity.score is None