"""Public Open Data Operations: GeoJSON & CSV Export."""

from __future__ import annotations

import csv
import io
from typing import Any

from civitas_api.operations.reports import list_incidents
from civitas_geo.hex_index import geo_to_h3
from civitas_knowledge.transparency import apply_differential_privacy_jitter, redact_pii_text


def generate_public_geojson_feature_collection(limit: int = 200) -> dict[str, Any]:
    """Generates an RFC 7946 GeoJSON FeatureCollection with privacy jitter and PII redaction."""
    incidents = list_incidents(limit=limit)

    features = []
    for inc in incidents:
        inc_id = inc.get("incident_id", "inc-unknown")
        raw_lat = float(inc.get("latitude", 20.29614))
        raw_lon = float(inc.get("longitude", 85.82451))

        # Apply differential privacy spatial jitter (±25m)
        jit_lat, jit_lon = apply_differential_privacy_jitter(raw_lat, raw_lon, seed_key=inc_id)

        # Redact any PII from description
        clean_desc = redact_pii_text(inc.get("description", ""))

        hex_cell = geo_to_h3(raw_lat, raw_lon, 8)  # type: ignore[arg-type]

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [jit_lon, jit_lat],
            },
            "properties": {
                "incident_id": inc_id,
                "category": inc.get("category", "general_hazard"),
                "status": inc.get("status", "open"),
                "reported_at": str(inc.get("reported_at", "")),
                "description_sanitized": clean_desc,
                "h3_hex_cell": hex_cell,
                "assigned_department": inc.get("assigned_department", "public_works"),
                "privacy_preserved": True,
            },
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def generate_public_csv_export(limit: int = 500) -> str:
    """Generates a sanitized CSV string for public data analytics."""
    incidents = list_incidents(limit=limit)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "incident_id",
        "category",
        "status",
        "reported_at",
        "latitude_jittered",
        "longitude_jittered",
        "h3_hex_cell",
        "assigned_department",
        "sanitized_description",
    ])

    for inc in incidents:
        inc_id = inc.get("incident_id", "inc-unknown")
        raw_lat = float(inc.get("latitude", 20.29614))
        raw_lon = float(inc.get("longitude", 85.82451))
        jit_lat, jit_lon = apply_differential_privacy_jitter(raw_lat, raw_lon, seed_key=inc_id)
        clean_desc = redact_pii_text(inc.get("description", ""))
        hex_cell = geo_to_h3(raw_lat, raw_lon, 8)  # type: ignore[arg-type]

        writer.writerow([
            inc_id,
            inc.get("category", "general_hazard"),
            inc.get("status", "open"),
            str(inc.get("reported_at", "")),
            jit_lat,
            jit_lon,
            hex_cell,
            inc.get("assigned_department", "public_works"),
            clean_desc,
        ])

    return output.getvalue()
