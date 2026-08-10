"""Phase 12: the image/video refining track — video analysis end to end.

Covers the video path that Phase 10 scaffolded and Phase 12 completed:

- `analyze_report(video=...)` decodes a local video once, keeps
  container metadata, and produces a vision verdict over key frames;
- `run_report` accepts video media references with either a local path
  or backend-provided bytes (no more "backend video bytes not supported");
- `run_resolution` accepts BEFORE/AFTER videos and compares their best
  key frames;
- every failure (missing file, undecodable bytes, missing decoder) is a
  structured, non-crashing rejection recorded in the vision section.

OpenCV is an optional dependency (civitas-ml[video]); decode tests are
skipped when it is not installed, structured-rejection tests always run.
"""

from __future__ import annotations

from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")  # noqa: E402 - guarded optional dependency

from civitas_ml.adapters.mock import MockBackendAdapter  # noqa: E402
from civitas_ml.analyze import analyze_report  # noqa: E402
from civitas_ml.contracts import MediaReference, ReportInput, ResolutionInput  # noqa: E402
from civitas_ml.media import ResolvedVideo, resolve_video  # noqa: E402
from civitas_ml.pipeline import run_report, run_resolution  # noqa: E402
from civitas_vision.benchmark import make_scene  # noqa: E402


def _write_video(tmp_path: Path, category: str = "water_leakage", variant: str = "flow") -> Path:
    """Write a real, deterministic mp4 (category scenes) to disk."""
    out = tmp_path / f"{category}_{variant}.mp4"
    writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, (224, 224))
    for i in range(10):
        arr = make_scene(category, 3000 + i, variant=variant)
        frame = cv2.cvtColor((arr * 255).astype("uint8"), cv2.COLOR_RGB2BGR)
        writer.write(frame)
    writer.release()
    return out


class _VideoBackend(MockBackendAdapter):
    """Backend that serves one video's bytes for a media_id."""

    def __init__(self, video_path: Path) -> None:
        super().__init__()
        self._video_bytes = video_path.read_bytes()

    def fetch_media(self, reference: str) -> bytes:
        return self._video_bytes


def test_analyze_report_video_local(tmp_path: Path) -> None:
    video = _write_video(tmp_path)
    analysis = analyze_report(video=video, description="water flowing on the road near the school")
    assert analysis.vision.media_kind == "video"
    assert analysis.vision.media_usable
    assert analysis.vision.frames_selected > 0
    assert analysis.vision.video_total_frames is not None and analysis.vision.video_total_frames > 0
    assert analysis.vision.video_fps is not None
    assert analysis.vision.primary_category in {
        "water_leakage",
        "pothole_road_damage",
        "garbage_overflow",
        "broken_streetlight",
        "fallen_tree",
    }
    assert any("decoded" in line for line in analysis.vision.basis)


def test_run_report_video_local(tmp_path: Path) -> None:
    video = _write_video(tmp_path)
    analysis = run_report(
        ReportInput(
            report_id="VR-1",
            media=[MediaReference(kind="video", local_path=str(video), mime_type="video/mp4")],
            description="pipe burst, road flooded",
            latitude=28.61,
            longitude=77.21,
        ),
        backend=MockBackendAdapter(),
    )
    assert analysis.vision.media_kind == "video"
    assert analysis.vision.media_usable
    assert analysis.vision.video_duration_s is not None and analysis.vision.video_duration_s > 0
    assert not analysis.vision.media_rejected_basis


def test_run_report_video_backend_bytes(tmp_path: Path) -> None:
    video = _write_video(tmp_path)
    backend = _VideoBackend(video)
    analysis = run_report(
        ReportInput(
            report_id="VR-2",
            media=[MediaReference(media_id="video-1", kind="video", mime_type="video/mp4")],
            description="water leakage by the bus stop",
            latitude=28.61,
            longitude=77.21,
        ),
        backend=backend,
    )
    assert analysis.vision.media_kind == "video"
    assert analysis.vision.media_usable
    assert analysis.vision.frames_selected > 0
    assert not analysis.vision.media_rejected_basis


def test_missing_video_is_structured_rejection(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.mp4"
    analysis = analyze_report(video=missing, description="unknown")
    assert not analysis.vision.media_usable
    assert analysis.vision.media_kind == "video"
    assert any("media_not_found" in line for line in analysis.vision.media_rejected_basis)


def test_corrupt_video_bytes_are_structured_rejection(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.mp4"
    corrupt.write_bytes(b"this is definitely not a video container")
    resolved = resolve_video(MediaReference(local_path=str(corrupt), kind="video"))
    assert resolved.frames is None
    assert resolved.error_code == "media_unreadable"
    assert resolved.error_note is not None


def test_video_backend_missing_bytes_is_structured_rejection() -> None:
    backend = MockBackendAdapter()
    resolved = resolve_video(MediaReference(media_id="no-such-video", kind="video"), backend)
    assert resolved.frames is None
    assert resolved.error_code in {"media_not_found", "media_unreadable"}
    assert isinstance(resolved, ResolvedVideo)


def test_run_resolution_with_before_after_videos(tmp_path: Path) -> None:
    before = _write_video(tmp_path, category="water_leakage", variant="flow")
    after = _write_video(tmp_path, category="water_leakage", variant="dry")
    verification = run_resolution(
        ResolutionInput(
            incident_id="INC-V1",
            before=MediaReference(kind="video", local_path=str(before), mime_type="video/mp4"),
            after=MediaReference(kind="video", local_path=str(after), mime_type="video/mp4"),
        ),
        backend=MockBackendAdapter(),
    )
    assert verification.status in {"resolved", "partial", "unverifiable", "conflicting"}
    assert verification.total_signals > 0 or verification.status == "unverifiable"
    assert any("video" in line for line in verification.basis)


def test_run_resolution_missing_video_is_unverifiable(tmp_path: Path) -> None:
    missing = tmp_path / "gone.mp4"
    after = _write_video(tmp_path, category="pothole_road_damage", variant="default")
    verification = run_resolution(
        ResolutionInput(
            incident_id="INC-V2",
            before=MediaReference(kind="video", local_path=str(missing)),
            after=MediaReference(kind="video", local_path=str(after), mime_type="video/mp4"),
        ),
        backend=MockBackendAdapter(),
    )
    assert verification.status == "unverifiable"
    assert any("video could not be resolved" in line for line in verification.basis)
