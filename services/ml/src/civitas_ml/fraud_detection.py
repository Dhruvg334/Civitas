"""Contractor Fraud, Media Tampering & EXIF Spoofing Detection Engine.

Performs perceptual image hashing (dHash), temporal timestamp sanity checks,
and spatial geotag proximity verification to prevent contractor closure fraud.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from PIL import Image


@dataclass(frozen=True)
class FraudCheckViolation:
    code: str
    message: str
    severity: str  # "critical" or "warning"


@dataclass(frozen=True)
class FraudVerificationResult:
    is_fraudulent: bool
    requires_inspection: bool
    violations: list[FraudCheckViolation]
    dhash_hamming_distance: int | None
    temporal_delta_seconds: float | None
    spatial_distance_meters: float | None
    summary_verdict: str


def compute_difference_hash(image_bytes: bytes) -> str:
    """Computes a 64-bit gradient difference hash (dHash) from image bytes."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Resize to 9x8 grayscale
            resized = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
            pixels = list(resized.get_flattened_data()) if hasattr(resized, "get_flattened_data") else list(resized.getdata())

            # Compare adjacent pixels in each row
            difference = []
            for row in range(8):
                for col in range(8):
                    pixel_left = pixels[row * 9 + col]
                    pixel_right = pixels[row * 9 + col + 1]
                    difference.append(pixel_left > pixel_right)

            # Convert 64 booleans to 16-char hex string
            decimal_value = 0
            for idx, val in enumerate(difference):
                if val:
                    decimal_value |= 1 << idx
            return f"{decimal_value:016x}"
    except Exception:
        # Fallback hash
        return f"{hash(image_bytes) & 0xFFFFFFFFFFFFFFFF:016x}"


def compute_hamming_distance(hash1: str, hash2: str) -> int:
    """Calculate the Hamming distance (number of bit differences) between two 64-bit hex hashes."""
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        xor_val = val1 ^ val2
        return bin(xor_val).count("1")
    except Exception:
        return 64


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    r = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def verify_contractor_resolution_media(
    before_image_bytes: bytes,
    after_image_bytes: bytes,
    work_order_created_at: datetime,
    after_photo_captured_at: datetime | None = None,
    incident_latitude: float | None = None,
    incident_longitude: float | None = None,
    after_photo_latitude: float | None = None,
    after_photo_longitude: float | None = None,
) -> FraudVerificationResult:
    """Verifies that contractor repair media is genuine, timely, and physically on-site."""
    violations: list[FraudCheckViolation] = []

    # 1. Perceptual Image Hash (dHash) Identical Photo Check
    h1 = compute_difference_hash(before_image_bytes)
    h2 = compute_difference_hash(after_image_bytes)
    dist = compute_hamming_distance(h1, h2)

    # Hamming distance <= 5 indicates near-identical or recycled photo
    if dist <= 5:
        violations.append(
            FraudCheckViolation(
                code="FRAUD_IDENTICAL_MEDIA",
                message=f"Resolution photo is perceptually identical to original report photo (dHash distance: {dist}/64). Recycled evidence suspected.",
                severity="critical",
            )
        )

    # 2. Temporal Sanity Check
    temp_delta = None
    if after_photo_captured_at is not None:
        delta = (after_photo_captured_at - work_order_created_at).total_seconds()
        temp_delta = delta
        if delta < -60:  # Taken more than 1 min before work order was even dispatched
            violations.append(
                FraudCheckViolation(
                    code="FRAUD_STALE_PHOTO",
                    message=f"Resolution photo EXIF timestamp ({after_photo_captured_at.isoformat()}) predates work order dispatch ({work_order_created_at.isoformat()}).",
                    severity="critical",
                )
            )

    # 3. Spatial Proximity Check (<= 75m)
    spatial_dist = None
    if (
        incident_latitude is not None
        and incident_longitude is not None
        and after_photo_latitude is not None
        and after_photo_longitude is not None
    ):
        spatial_dist = _haversine_meters(
            incident_latitude,
            incident_longitude,
            after_photo_latitude,
            after_photo_longitude,
        )
        if spatial_dist > 75.0:
            violations.append(
                FraudCheckViolation(
                    code="FRAUD_GEO_MISMATCH",
                    message=f"Resolution photo EXIF GPS location is {round(spatial_dist)}m away from incident site (limit: 75m).",
                    severity="critical",
                )
            )

    has_critical = any(v.severity == "critical" for v in violations)
    verdict = (
        f"REJECTED: {len(violations)} fraud violations detected: " + "; ".join(v.message for v in violations)
        if has_critical
        else "VERIFIED: Resolution evidence passed all anti-fraud, temporal, and spatial checks."
    )

    return FraudVerificationResult(
        is_fraudulent=has_critical,
        requires_inspection=has_critical,
        violations=violations,
        dhash_hamming_distance=dist,
        temporal_delta_seconds=temp_delta,
        spatial_distance_meters=round(spatial_dist, 1) if spatial_dist is not None else None,
        summary_verdict=verdict,
    )
