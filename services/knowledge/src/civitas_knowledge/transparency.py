"""Differential Privacy & PII Scrubbing Engine for Open Data Transparency.

Provides automated redaction of personal identifiable information (PII)
and applies spatial perturbation (differential privacy jitter) to public feeds.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any


def redact_pii_text(text: str) -> str:
    """Scrubs personal identifiable information (PII) from citizen report text."""
    if not text:
        return ""

    sanitized = text

    # 1. Phone numbers (international and 10-digit formats)
    phone_pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10}\b"
    sanitized = re.sub(phone_pattern, "[PHONE_REDACTED]", sanitized)

    # 2. Email addresses
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    sanitized = re.sub(email_pattern, "[EMAIL_REDACTED]", sanitized)

    # 3. Vehicle License Plate patterns (e.g. DL 01 AB 1234, KA05MH1234)
    plate_pattern = r"\b[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4}\b"
    sanitized = re.sub(plate_pattern, "[VEHICLE_PLATE_REDACTED]", sanitized)

    # 4. Door / Flat numbers (e.g. Flat 402, House No 12B, Apt 3A)
    flat_pattern = r"\b(?:Flat|House|Apt|Apartment|Plot|Door|Room|Villa)\s*(?:No\.?|#)?\s*[0-9]+[A-Za-z]?\b"
    sanitized = re.sub(flat_pattern, "[ADDRESS_REDACTED]", sanitized, flags=re.IGNORECASE)

    return sanitized


def apply_differential_privacy_jitter(
    latitude: float,
    longitude: float,
    seed_key: str = "",
    epsilon_meters: float = 25.0,
) -> tuple[float, float]:
    """Applies bounded, deterministic spatial jitter to protect residential privacy on public feeds."""
    # Compute deterministic pseudo-random offset from seed_key
    seed_str = f"{seed_key}:{latitude:.6f}:{longitude:.6f}"
    digest = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    val1 = int(digest[0:8], 16) / 0xFFFFFFFF
    val2 = int(digest[8:16], 16) / 0xFFFFFFFF

    # Map to [-epsilon_meters, +epsilon_meters]
    offset_x_m = (val1 * 2.0 - 1.0) * epsilon_meters
    offset_y_m = (val2 * 2.0 - 1.0) * epsilon_meters

    # 1 degree latitude ~ 111,139 meters
    # 1 degree longitude ~ 111,139 * cos(latitude) meters
    delta_lat = offset_y_m / 111139.0
    rad_lat = math.radians(latitude)
    cos_lat = max(0.1, math.cos(rad_lat))
    delta_lon = offset_x_m / (111139.0 * cos_lat)

    jittered_lat = round(latitude + delta_lat, 6)
    jittered_lon = round(longitude + delta_lon, 6)

    return jittered_lat, jittered_lon
