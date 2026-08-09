"""Media resolution + validation (Phase 10).

Turns a `MediaReference` (local path or backend reference) into a
validated PIL image for the vision pipeline. Everything that can go
wrong is a *structured* error — the pipeline never crashes on bad media
and never guesses.

Outcomes for the vision stage (documented contract):
- usable           -> the image passes the quality gate and is classified;
- blurred          -> quality gate rejects (blur/exposure/resolution);
- missing          -> reference/file does not exist          (media_not_found);
- unsupported      -> bytes are not decodable as an image     (media_unreadable);
- invalid kind     -> video declared as image or vice versa   (media_invalid_kind).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, UnidentifiedImageError

from civitas_ml.contracts import MediaReference
from civitas_ml.errors import (
    CODE_MEDIA_INVALID_KIND,
    CODE_MEDIA_NOT_FOUND,
    CODE_MEDIA_UNREADABLE,
    CODE_MEDIA_UNSUPPORTED,
)

if TYPE_CHECKING:
    from civitas_ml.adapters.base import BackendAdapter

# The pipeline decodes image media only; video goes to the video path.
SUPPORTED_IMAGE_MIME = ("image/png", "image/jpeg", "image/jpg", "image/webp")


@dataclass(frozen=True)
class ResolvedMedia:
    """One resolved, schema-validated media item ready for the pipeline."""

    reference: MediaReference
    image: Image.Image | None  # set for kind=image after decoding
    source: str  # 'local' | 'backend'
    bytes_size: int = 0
    error_code: str | None = None
    error_note: str | None = None


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


def resolve_media(reference: MediaReference, backend: "BackendAdapter | None" = None) -> ResolvedMedia:
    """Resolve one media reference to a decoded image or a structured error."""
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
    if reference.kind == "video":
        return ResolvedMedia(
            reference=reference,
            image=None,
            source="backend",
            error_code=CODE_MEDIA_INVALID_KIND,
            error_note="video media cannot decode through the image path",
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


__all__ = ["ResolvedMedia", "resolve_media", "SUPPORTED_IMAGE_MIME"]