"""Phase 11 failure-behaviour tests: the pipeline fails structured, never guesses.

Covers the boundary/rules in AGENTS.md:
- backend payloads violating the shared contract surface as
  MalformedResponseError with the fixture named, not silent fallbacks;
- missing operational files surface as FileNotFoundError (a real outage),
  never as fabricated empty results;
- uncertain vision (low-confidence or out-of-distribution media) is recorded
  as `uncertainty` notes with rationale instead of asserted as fact.
"""

from __future__ import annotations

import datetime

import numpy as np
import pytest
from civitas_ml.adapters.mock import MockBackendAdapter
from civitas_ml.analyze import (
    analyze_report,
    build_vision_section,
    collect_vision_uncertainty,
)
from civitas_ml.contracts import NearbyCandidatesRequest, VisionSection
from civitas_ml.errors import MalformedResponseError
from PIL import Image


def _candidate_request(report_id: str = "CL-018") -> NearbyCandidatesRequest:
    return NearbyCandidatesRequest(
        report_id=report_id,
        latitude=28.6139,
        longitude=77.2090,
        submitted_at="2026-03-01T12:00:00+00:00",
    )


def test_malformed_candidates_fixture_surfaces_structured_error() -> None:
    adapter = MockBackendAdapter(malformed_paths={"candidates:CL-018"})
    with pytest.raises(MalformedResponseError) as excinfo:
        adapter.fetch_nearby_candidates(_candidate_request("CL-018"))
    assert "does not match the contract" in str(excinfo.value)
    assert "mock_candidates.json" in excinfo.value.details["fixture"]


def test_malformed_landmarks_fixture_surfaces_structured_error() -> None:
    adapter = MockBackendAdapter(malformed_paths={"landmarks"})
    with pytest.raises(MalformedResponseError) as excinfo:
        adapter.fetch_landmarks()
    assert "does not match the contract" in str(excinfo.value)
    assert "mock_landmarks.json" in excinfo.value.details["fixture"]


def test_healthy_fixtures_do_not_trigger_failure_path() -> None:
    adapter = MockBackendAdapter()
    response = adapter.fetch_nearby_candidates(_candidate_request("CL-018"))
    assert response.count == len(response.candidates)
    assert adapter.fetch_landmarks().landmarks


def test_missing_candidates_file_surfaces_as_file_not_found(tmp_path) -> None:
    adapter = MockBackendAdapter(candidates_file=tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        adapter.fetch_nearby_candidates(_candidate_request())


def test_missing_media_reference_never_fabricates_bytes() -> None:
    adapter = MockBackendAdapter()
    with pytest.raises(FileNotFoundError):
        adapter.fetch_media("mock:does-not-exist.png")


def test_confident_vision_has_no_uncertainty_notes() -> None:
    section, _ = build_vision_section(None)
    assert section.media_usable is False
    assert collect_vision_uncertainty(section) == []

    confident = VisionSection(
        media_usable=True,
        primary_category="water_leakage",
        confidence=0.95,
        ood_ratio=1.1,
        media_kind="image",
        frames_selected=1,
    )
    assert collect_vision_uncertainty(confident) == []


def test_low_confidence_classification_is_flagged_not_fact() -> None:
    section = VisionSection(
        media_usable=True,
        primary_category="broken_streetlight",
        confidence=0.31,
        ood_ratio=1.0,
        media_kind="image",
        frames_selected=1,
    )
    notes = collect_vision_uncertainty(section)
    assert any("low-confidence classification" in note for note in notes)
    assert "best-effort guess" not in "\n".join(notes)


def test_low_confidence_note_ignored_when_media_unusable() -> None:
    section = VisionSection(
        media_usable=False,
        primary_category=None,
        confidence=0.0,
        media_kind="none",
    )
    assert collect_vision_uncertainty(section) == []


def test_out_of_distribution_media_is_flagged_as_guess() -> None:
    section = VisionSection(
        media_usable=True,
        primary_category="pothole_road_damage",
        confidence=0.97,
        ood_ratio=3.2,
        media_kind="image",
        frames_selected=1,
    )
    notes = collect_vision_uncertainty(section)
    assert any("out-of-distribution media" in note for note in notes)
    assert any("best-effort guess" in note for note in notes)


def test_both_uncertainty_modes_can_fire_together() -> None:
    section = VisionSection(
        media_usable=True,
        primary_category="garbage_accumulation",
        confidence=0.2,
        ood_ratio=4.0,
        media_kind="image",
        frames_selected=1,
    )
    notes = collect_vision_uncertainty(section)
    assert len(notes) == 2


def test_random_noise_image_is_not_asserted_as_a_category() -> None:
    rng = np.random.default_rng(7)
    analysis = analyze_report(
        image=Image.fromarray(rng.integers(0, 256, (320, 320, 3), dtype=np.uint8)),
        description="random noise feed",
        report_id="CL-OOD-001",
        timestamp=datetime.datetime(2026, 8, 10, 10, 0, tzinfo=datetime.timezone.utc),
    )
    assert analysis.vision.ood_ratio >= 2.0
    assert analysis.vision.uncertainty
    assert any("out-of-distribution media" in note for note in analysis.vision.uncertainty)
    assert any(
        "out-of-distribution" in line for line in analysis.vision.basis
    )


def test_representative_fixture_image_stays_confident() -> None:
    from civitas_vision.benchmark import make_image

    analysis = analyze_report(
        image=make_image("water_leakage", 7101, "flow"),
        description="water leaking near sunrise school",
        report_id="CL-OK-001",
        timestamp=datetime.datetime(2026, 8, 10, 10, 0, tzinfo=datetime.timezone.utc),
    )
    assert analysis.vision.media_usable is True
    assert analysis.vision.ood_ratio < 2.0
    assert analysis.vision.uncertainty == []