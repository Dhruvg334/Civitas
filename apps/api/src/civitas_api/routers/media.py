"""Media upload route for citizen reports.

Single endpoint: POST /api/v1/reports/{report_id}/media

Accepts multipart/form-data with one file. The MIME type is validated
against the allowlist in Pavit's ML contracts (image/png, image/jpeg,
image/webp, video/mp4, video/webm, video/quicktime, video/x-matroska).
The file is uploaded to the configured storage backend and a row is
written to the `media` table. Returns a signed URL the workflow can
hand to the ML service.

A citizen can attach media to their own report (CITIZEN role). Triage
and above can attach to anyone's report for backwards-compatibility
with the existing schema.
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from civitas_api.core.auth import Principal, Role, require_role
from civitas_api.core.envelope import error_envelope, success_envelope
from civitas_api.core.storage import get_storage
from civitas_api.operations import reports as reports_ops

router = APIRouter(prefix="/api/v1/reports", tags=["media"])

ALLOWED_IMAGE_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_VIDEO_MIME = {"video/mp4", "video/webm", "video/quicktime", "video/x-matroska"}
ALLOWED_MIME = ALLOWED_IMAGE_MIME | ALLOWED_VIDEO_MIME
MAX_BYTES = 50 * 1024 * 1024  # 50 MB


def _now() -> datetime:
    return datetime.now(UTC)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


@router.post("/{report_id}/media", status_code=status.HTTP_201_CREATED)
async def upload_media(
    report_id: str,
    principal: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
    file: Annotated[UploadFile, File()],
    captured_at: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    """Upload one media file for a report. Returns media_id + signed URL."""
    report = reports_ops.get_incident(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")

    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=error_envelope(
                code="UNSUPPORTED_MEDIA",
                message=f"mime {mime!r} not in allowlist; allowed: {sorted(ALLOWED_MIME)}",
                retryable=False,
            ),
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_envelope(
                code="EMPTY_FILE",
                message="uploaded file is empty",
                retryable=False,
            ),
        )
    if len(data) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_envelope(
                code="FILE_TOO_LARGE",
                message=f"file size {len(data)} exceeds limit {MAX_BYTES}",
                retryable=False,
            ),
        )

    kind = "video" if mime in ALLOWED_VIDEO_MIME else "image"
    ext_map = {
        "image/png": "png", "image/jpeg": "jpg", "image/jpg": "jpg", "image/webp": "webp",
        "video/mp4": "mp4", "video/webm": "webm",
        "video/quicktime": "mov", "video/x-matroska": "mkv",
    }
    ext = ext_map.get(mime, "bin")
    media_id = _gen_id("med")
    storage_path = f"{report_id}/{media_id}.{ext}"

    try:
        storage = get_storage()
        put_path = storage.put(storage_path, data, mime)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_envelope(
                code="STORAGE_ERROR",
                message=f"failed to write media: {exc}",
                retryable=True,
            ),
        ) from exc

    parsed_captured_at: datetime | None = None
    if captured_at:
        try:
            parsed_captured_at = datetime.fromisoformat(captured_at)
        except ValueError:
            parsed_captured_at = None

    now = _now()
    try:
        with reports_ops.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO media "
                "(media_id, incident_id, kind, mime_type, storage_path, "
                "bytes_size, captured_at, uploaded_at, uploaded_by) "
                "VALUES (%(id)s, %(i)s, %(k)s, %(m)s, %(p)s, %(b)s, "
                "%(cap)s, %(now)s, %(by)s)",
                {
                    "id": media_id,
                    "i": report_id,
                    "k": kind,
                    "m": mime,
                    "p": put_path,
                    "b": len(data),
                    "cap": parsed_captured_at,
                    "now": now,
                    "by": principal.user_id,
                },
            )
            conn.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_envelope(
                code="PERSISTENCE_ERROR",
                message=f"failed to record media row: {exc}",
                retryable=True,
            ),
        ) from exc

    try:
        signed = get_storage().signed_url(storage_path, ttl_seconds=3600)
    except Exception:  # noqa: BLE001
        signed = put_path  # fall back to storage path

    return success_envelope({
        "media_id": media_id,
        "report_id": report_id,
        "kind": kind,
        "mime_type": mime,
        "bytes_size": len(data),
        "storage_path": put_path,
        "signed_url": signed,
        "uploaded_at": now.isoformat(),
        "uploaded_by": principal.user_id,
    })


@router.get("/{report_id}/media")
def list_media(
    report_id: str,
    _principal: Annotated[Principal, Depends(require_role(Role.CITIZEN))],
) -> dict[str, Any]:
    """List media for a report. Includes signed URLs (1h TTL)."""
    if reports_ops.get_incident(report_id) is None:
        raise HTTPException(status_code=404, detail="report not found")
    rows = reports_ops.list_media_for_incident(report_id)
    out = []
    for r in rows:
        try:
            signed = get_storage().signed_url(r["storage_path"], ttl_seconds=3600)
        except Exception:  # noqa: BLE001
            signed = r["storage_path"]
        out.append({
            "media_id": r["media_id"],
            "kind": r["kind"],
            "mime_type": r["mime_type"],
            "bytes_size": r["bytes_size"],
            "storage_path": r["storage_path"],
            "signed_url": signed,
            "uploaded_at": (
                r["uploaded_at"].isoformat()
                if hasattr(r.get("uploaded_at"), "isoformat")
                else r.get("uploaded_at")
            ),
            "uploaded_by": r.get("uploaded_by"),
        })
    return success_envelope({
        "report_id": report_id,
        "media": out,
        "count": len(out),
    })
