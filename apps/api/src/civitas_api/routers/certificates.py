"""Digital Municipal Audit Certificate Router."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from civitas_api.core.envelope import envelope, error_envelope
from civitas_api.operations.audit_certificate import generate_municipal_audit_certificate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resolutions", tags=["Resolution Audit Certificates"])


@router.get("/{incident_id}/certificate")
async def get_resolution_audit_certificate(incident_id: str):
    """Retrieves the tamper-proof cryptographic SHA-256 municipal audit certificate for an incident."""
    try:
        cert = generate_municipal_audit_certificate(incident_id)
        return envelope({
            "certificate_id": cert.certificate_id,
            "incident_id": cert.incident_id,
            "issued_at": cert.issued_at,
            "governing_municipality": cert.governing_municipality,
            "sha256_cryptographic_digest": cert.sha256_cryptographic_digest,
            "lifecycle_payload": cert.lifecycle_payload,
            "verification_url": cert.verification_url,
        })
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=error_envelope(
                code="INCIDENT_NOT_FOUND",
                message=str(exc),
            ),
        ) from exc
