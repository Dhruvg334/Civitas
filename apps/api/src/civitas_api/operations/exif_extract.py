"""EXIF Geotag extraction and privacy-sanitizing image processor.

Extracts GPS coordinates and capture timestamps from photo EXIF metadata
while stripping camera make/model, device serial numbers, and personal
device identifiers prior to persistent storage.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExifExtractionResult:
    latitude: float | None
    longitude: float | None
    altitude_m: float | None
    captured_at: datetime | None
    has_exif: bool
    stripped_tags_count: int
    cleaned_bytes: bytes


def _dms_to_decimal(degrees: Any, minutes: Any, seconds: Any, ref: str) -> float:
    """Convert degrees, minutes, seconds rational tuples to decimal degrees."""
    def _val(x: Any) -> float:
        try:
            if isinstance(x, tuple) and len(x) == 2:
                return float(x[0]) / float(x[1]) if x[1] != 0 else 0.0
            if hasattr(x, "numerator") and hasattr(x, "denominator"):
                return float(x.numerator) / float(x.denominator) if x.denominator != 0 else 0.0
            return float(x)
        except Exception:
            return 0.0

    d = _val(degrees)
    m = _val(minutes)
    s = _val(seconds)
    dec = d + (m / 60.0) + (s / 3600.0)
    if ref.upper() in ("S", "W"):
        dec = -dec
    return dec


def extract_and_sanitize_exif(image_bytes: bytes, mime_type: str = "image/jpeg") -> ExifExtractionResult:
    """Extract GPS coordinates and capture date from image bytes and sanitize

    device tracking tags.
    """
    if not image_bytes or not mime_type.lower().startswith("image/"):
        return ExifExtractionResult(
            latitude=None,
            longitude=None,
            altitude_m=None,
            captured_at=None,
            has_exif=False,
            stripped_tags_count=0,
            cleaned_bytes=image_bytes,
        )

    try:
        from PIL import ExifTags, Image

        with Image.open(io.BytesIO(image_bytes)) as img:
            exif = img.getexif()
            if not exif:
                return ExifExtractionResult(
                    latitude=None,
                    longitude=None,
                    altitude_m=None,
                    captured_at=None,
                    has_exif=False,
                    stripped_tags_count=0,
                    cleaned_bytes=image_bytes,
                )

            lat: float | None = None
            lon: float | None = None
            alt: float | None = None
            captured_at: datetime | None = None
            stripped_count = 0

            # 1. Parse IFD / GPS Info
            gps_ifd = None
            for key, val in ExifTags.TAGS.items():
                if val == "GPSInfo":
                    gps_ifd = exif.get_ifd(key)
                    break

            if gps_ifd:
                gps_tags = {ExifTags.GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
                if "GPSLatitude" in gps_tags and "GPSLatitudeRef" in gps_tags:
                    coords = gps_tags["GPSLatitude"]
                    ref = gps_tags["GPSLatitudeRef"]
                    if len(coords) == 3:
                        lat = _dms_to_decimal(coords[0], coords[1], coords[2], ref)

                if "GPSLongitude" in gps_tags and "GPSLongitudeRef" in gps_tags:
                    coords = gps_tags["GPSLongitude"]
                    ref = gps_tags["GPSLongitudeRef"]
                    if len(coords) == 3:
                        lon = _dms_to_decimal(coords[0], coords[1], coords[2], ref)

                if "GPSAltitude" in gps_tags:
                    raw_alt = gps_tags["GPSAltitude"]
                    if isinstance(raw_alt, tuple) and len(raw_alt) == 2:
                        alt = float(raw_alt[0]) / float(raw_alt[1]) if raw_alt[1] != 0 else None
                    else:
                        alt = float(raw_alt)

            # 2. Parse DateTimeOriginal
            date_str = exif.get(0x9003) or exif.get(0x0132)  # DateTimeOriginal or DateTime
            if date_str and isinstance(date_str, str):
                try:
                    captured_at = datetime.strptime(date_str.strip(), "%Y:%m:%d %H:%M:%S")
                except Exception:
                    pass

            # 3. Privacy Stripping: Remove hardware serials, make/model, author
            privacy_tag_names = {
                "Make",
                "Model",
                "Software",
                "Artist",
                "Copyright",
                "BodySerialNumber",
                "CameraOwnerName",
                "LensMake",
                "LensModel",
                "LensSerialNumber",
                "DeviceSettingDescription",
            }
            tags_to_delete = [
                tag_id
                for tag_id, name in ExifTags.TAGS.items()
                if name in privacy_tag_names and tag_id in exif
            ]
            for tag_id in tags_to_delete:
                del exif[tag_id]
                stripped_count += 1

            # 4. Save cleaned image
            out_buf = io.BytesIO()
            fmt = img.format or ("JPEG" if "jpeg" in mime_type.lower() else "PNG")
            img.save(out_buf, format=fmt, exif=exif)
            cleaned = out_buf.getvalue()

            # Validate coordinate bounds
            if lat is not None and not (-90.0 <= lat <= 90.0):
                lat = None
            if lon is not None and not (-180.0 <= lon <= 180.0):
                lon = None

            return ExifExtractionResult(
                latitude=round(lat, 6) if lat is not None else None,
                longitude=round(lon, 6) if lon is not None else None,
                altitude_m=round(alt, 1) if alt is not None else None,
                captured_at=captured_at,
                has_exif=True,
                stripped_tags_count=stripped_count,
                cleaned_bytes=cleaned if cleaned else image_bytes,
            )

    except Exception as err:
        logger.warning("EXIF extraction encountered non-fatal error: %s", err)
        return ExifExtractionResult(
            latitude=None,
            longitude=None,
            altitude_m=None,
            captured_at=None,
            has_exif=False,
            stripped_tags_count=0,
            cleaned_bytes=image_bytes,
        )
