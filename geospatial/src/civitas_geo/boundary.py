"""PostGIS Boundary: the spatial definition of the operational area.

Phase 2 artifact. One shared `OperationalBoundary` gates both halves of the
spatial pipeline:

- location validation (is a report geographically plausible enough to enter),
- candidate retrieval (PostGIS envelope pre-filter on `location_geom`).

The default describes the demo city; production deployments override it with
authority-provided polygons (the model accepts a bounding box today and is
forward-compatible with polygon boundaries). The boundary is observable
configuration, not model inference: any consumer can read `description` and
`source` to attribute where coverage came from.
"""

from __future__ import annotations

from civitas_geo.models import GeoPoint, OperationalBoundary

DEFAULT_BOUNDARY: OperationalBoundary = OperationalBoundary(
    name="civitas-demo-city",
    bbox=(28.55, 77.15, 28.66, 77.27),
    source="seed config",
)


def point_in_boundary(point: GeoPoint, boundary: OperationalBoundary | None = None) -> bool:
    """True when a point falls inside the operational boundary."""
    boundary = boundary or DEFAULT_BOUNDARY
    return boundary.contains(point.latitude, point.longitude)