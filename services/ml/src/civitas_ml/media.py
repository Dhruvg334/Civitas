"""Media resolution + validation (Phase 10; video path refined Phase 12).

Turns a `MediaReference` (local path or backend reference) into
validated, pipeline-ready media. Images decode to a PIL image; videos
decode to a bounded set of downscaled frames plus duration metadata.
Everything that can go wrong is a *structured* error — the pipeline
never crashes on bad media and never guesses.

Outcomes for the vision stage (documented contract):
- usable           -> the media passes the quality gate and is classified;
- blurred          -> quality gate rejects (blur/exposure/resolution);
- missing          -> reference/file does not exist          (media_not_found);
- unsupported      -> bytes are not decodable as media        (media_unreadable);
- invalid kind     -> image declared as video or vice versa   (media_invalid_kind);
- dependency       -> video decoder (OpenCV) not installed    (dependency_missing).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, UnidentifiedImageError

from civitas_ml.contracts import MediaReference
from civitas_ml.errors import (
    CODE_DEPENDENCY_MISSING,
    CODE_MEDIA_INVALID_KIND,
    CODE_MEDIA_NOT_FOUND,
    CODE_MEDIA_UNREADABLE,
    CODE_MEDIA_UNSUPPORTED,
)

if TYPE_CHECKING:
    from civitas_ml.adapters.base import BackendAdapter

SUPPORTED_IMAGE_MIME = ("image/png", "image/jpeg", "image/jpg", "image/webp")
SUPPORTED_VIDEO_MIME = ("video/mp4", "video/webm", "video/quicktime", "video/x-matroska")

# Videos are sampled down to at most this many frames for analysis.
# 120 frames only covers ~1s of a high-fps (120) phone video; 300 keeps
# temporal coverage (~10s at 30 fps) while bounding decode cost. The
# vision key-frame picker then selects `top_k` across the duration.
MAX_VIDEO_FRAMES = 300
# Output resolution cap for analysed video frames (input-agnostic).
MAX_VIDEO_FRAME_PX = 1280


@dataclass(frozen=True)
class ResolvedMedia:
    """One resolved, schema-validated media item ready for the pipeline."""

    reference: MediaReference
    image: Image.Image | None  # set for kind=image after decoding
    source: str  # 'local' | 'backend'
    bytes_size: int = 0
    error_code: str | None = None
    error_note: str | None = None


@dataclass(frozen=True)
class ResolvedVideo:
    """One resolved video: decoded frames (bounded) + stream metadata.

    `frames` is set only on success and holds at most `MAX_VIDEO_FRAMES`
    downscaled frames. Stream metadata (`total_frames`, `fps`,
    `duration_s`) is measured from the container when the decoder reports
    it and is otherwise None — never guessed.
    """

    reference: MediaReference
    frames: tuple[Image.Image, ...] | None
    source: str  # 'local' | 'backend'
    total_frames: int = 0
    fps: float | None = None
    duration_s: float | None = None
    bytes_size: int = 0
    error_code: str | None = None
    error_note: str | None = None


class VideoDecodeError(RuntimeError):
    """Structured video decode failure (missing decoder, unreadable file)."""

    def __init__(self, code: str, note: str) -> None:
        super().__init__(note)
        self.code = code
        self.note = note


def _load_local_image(path: str, reference: MediaReference) -> ResolvedMedia:
    p = Path(path)
    if not p.exists():
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="local",
            error_code=CODE_MEDIA_NOT_FOUND,
            error_note=f"media file not found: {p}",
        )
    try:
        return ResolvedMedia(reference=reference, image=Image.open(p), source="local", bytes_size=p.stat().st_size)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="local",
            error_code=CODE_MEDIA_UNREADABLE,
            error_note=f"media bytes not decodable as an image: {exc}",
        )


def _decode_bytes(data: bytes, reference: MediaReference, source: str) -> ResolvedMedia:
    import io

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return ResolvedMedia(
            reference=reference,
            image=None,
            source=source,
            error_code=CODE_MEDIA_UNREADABLE,
            error_note=f"media bytes not decodable as an image: {exc}",
        )
    return ResolvedMedia(reference=reference, image=image, source=source, bytes_size=len(data))


def _decode_video_file(path: Path) -> tuple[tuple[Image.Image, ...], int, float | None, float | None]:
    """Decode a video file to bounded, downscaled frames + stream metadata.

    Raises `VideoDecodeError` (structured) for a missing decoder or for a
    file that yields no frames; the caller converts it into a
    `ResolvedVideo` error record.
    """
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:
        raise VideoDecodeError(
            CODE_DEPENDENCY_MISSING,
            "video decoding requires OpenCV (install the 'civitas-ml[video]' extra: "
            "opencv-python-headless)",
        ) from exc

    cap = cv2.VideoCapture(str(path))  # type: ignore[attr-defined]
    try:
        if not cap.isOpened():  # type: ignore[attr-defined]
            raise VideoDecodeError(
                CODE_MEDIA_UNREADABLE,
                f"video file could not be opened by the decoder: {path}",
            )
        fps = cap.get(cv2.CAP_PROP_FPS)  # type: ignore[attr-defined]
        container_total = cap.get(cv2.CAP_PROP_FRAME_COUNT)  # type: ignore[attr-defined]
        frames: list[Image.Image] = []
        for _ in range(MAX_VIDEO_FRAMES):
            ok, frame = cap.read()  # type: ignore[attr-defined]
            if not ok:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # type: ignore[attr-defined]
            img = Image.fromarray(rgb)
            if max(img.size) > MAX_VIDEO_FRAME_PX:
                scale = MAX_VIDEO_FRAME_PX / max(img.size)
                img = img.resize(
                    (max(1, int(img.width * scale)), max(1, int(img.height * scale))),
                    Image.Resampling.BILINEAR,
                )
            frames.append(img)
        if not frames:
            raise VideoDecodeError(
                CODE_MEDIA_UNREADABLE,
                f"video file decoded to zero frames: {path}",
            )
        duration_s = container_total / fps if fps and fps > 0 and container_total and container_total > 0 else None
        return tuple(frames), len(frames), (float(fps) if fps and fps > 0 else None), duration_s
    finally:
        cap.release()  # type: ignore[attr-defined]


def _video_error(
    reference: MediaReference, source: str, code: str, note: str
) -> ResolvedVideo:
    return ResolvedVideo(
        reference=reference, frames=None, source=source, error_code=code, error_note=note
    )


def _load_local_video(path: str, reference: MediaReference) -> ResolvedVideo:
    p = Path(path)
    if not p.exists():
        return _video_error(reference, "local", CODE_MEDIA_NOT_FOUND, f"video file not found: {p}")
    try:
        frames, total, fps, duration = _decode_video_file(p)
    except VideoDecodeError as exc:
        return _video_error(reference, "local", exc.code, exc.note)
    return ResolvedVideo(
        reference=reference,
        frames=frames,
        source="local",
        total_frames=total,
        fps=fps,
        duration_s=duration,
        bytes_size=p.stat().st_size,
    )


def _decode_video_bytes(
    data: bytes, reference: MediaReference, source: str, mime_type: str | None
) -> ResolvedVideo:
    if not data:
        return _video_error(reference, source, CODE_MEDIA_UNREADABLE, "video bytes are empty")
    suffix = ".mp4"
    if mime_type:
        lowered = mime_type.lower()
        suffix = {  # decoder-friendly extensions for known video mimes
            "video/webm": ".webm",
            "video/quicktime": ".mov",
            "video/x-matroska": ".mkv",
        }.get(lowered, ".mp4")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    try:
        frames, total, fps, duration = _decode_video_file(tmp_path)
    except VideoDecodeError as exc:
        return _video_error(reference, source, exc.code, exc.note)
    finally:
        tmp_path.unlink(missing_ok=True)
    return ResolvedVideo(
        reference=reference,
        frames=frames,
        source=source,
        total_frames=total,
        fps=fps,
        duration_s=duration,
        bytes_size=len(data),
    )


def resolve_video(reference: MediaReference, backend: BackendAdapter | None = None) -> ResolvedVideo:
    """Resolve one video reference to decoded frames + metadata, or a structured error."""
    if reference.local_path:
        return _load_local_video(reference.local_path, reference)
    if not reference.media_id:
        return _video_error(
            reference,
            "local",
            CODE_MEDIA_NOT_FOUND,
            "video reference has neither media_id nor local_path",
        )
    if backend is None:
        return _video_error(
            reference,
            "backend",
            CODE_MEDIA_UNSUPPORTED,
            "backend video reference supplied without a backend adapter",
        )
    if reference.mime_type and not reference.mime_type.lower().startswith("video/"):
        return _video_error(
            reference,
            "backend",
            CODE_MEDIA_INVALID_KIND,
            f"mime {reference.mime_type} is not a supported video type",
        )
    try:
        data = backend.fetch_media(reference.media_id)
    except FileNotFoundError as exc:
        return _video_error(reference, "backend", CODE_MEDIA_NOT_FOUND, str(exc))
    return _decode_video_bytes(data, reference, "backend", reference.mime_type)


def resolve_media(reference: MediaReference, backend: BackendAdapter | None = None) -> ResolvedMedia:
    """Resolve one media reference to a decoded image or a structured error."""
    if reference.kind == "video":
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="video",
            error_code=CODE_MEDIA_INVALID_KIND,
            error_note="video media must be resolved via resolve_video, not the image path",
        )
    if reference.local_path:
        return _load_local_image(reference.local_path, reference)
    if not reference.media_id:
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="local",
            error_code=CODE_MEDIA_NOT_FOUND,
            error_note="media reference has neither media_id nor local_path",
        )
    if backend is None:
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="backend",
            error_code=CODE_MEDIA_UNSUPPORTED,
            error_note="backend media reference supplied without a backend adapter",
        )
    if reference.mime_type and not reference.mime_type.lower().startswith("image/"):
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="backend",
            error_code=CODE_MEDIA_UNSUPPORTED,
            error_note=f"mime {reference.mime_type} is not a supported image type",
        )
    try:
        data = backend.fetch_media(reference.media_id)
    except FileNotFoundError as exc:
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="backend",
            error_code=CODE_MEDIA_NOT_FOUND,
            error_note=str(exc),
        )
    return _decode_bytes(data, reference, "backend")


__all__ = [
    "MAX_VIDEO_FRAMES",
    "SUPPORTED_IMAGE_MIME",
    "SUPPORTED_VIDEO_MIME",
    "ResolvedMedia",
    "ResolvedVideo",
    "VideoDecodeError",
    "resolve_media",
    "resolve_video",
]