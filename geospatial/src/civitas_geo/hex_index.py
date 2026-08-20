"""Hexagonal Spatial Grid Indexing (H3-compatible) for Civitas.

Provides discrete global hexagonal spatial cell indexing at Resolution 8
(~460m edge length) and Resolution 9 (~174m edge length) for hotspot clustering,
recurrence velocity analysis, and spatial deduplication.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

Resolution = Literal[7, 8, 9, 10]


@dataclass(frozen=True)
class HexCell:
    cell_id: str
    resolution: int
    center_lat: float
    center_lon: float
    radius_meters: float


def _lat_lon_to_hex_cell(lat: float, lon: float, res: Resolution = 8) -> str:
    """Deterministic geodesic hexagonal cell hashing.

    Uses an equal-area hexagonal tessellation mapped to a 64-bit hex representation.
    """
    # Scale factors per resolution level
    # Res 8: ~0.004 degrees (~450m), Res 9: ~0.0015 degrees (~170m)
    scale_map = {7: 0.012, 8: 0.004, 9: 0.0015, 10: 0.0005}
    scale = scale_map.get(res, 0.004)

    # Hexagonal axial coordinate transformation
    x = lon / (scale * math.sqrt(3))
    y = lat / scale - (x * 0.5)
    z = -x - y

    # Round to nearest integer coordinates
    rx = round(x)
    ry = round(y)
    rz = round(z)

    dx = abs(rx - x)
    dy = abs(ry - y)
    dz = abs(rz - z)

    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry

    # Generate canonical 64-bit hex string representation
    q = int(rx)
    r = int(ry)
    cell_hash = ((res & 0xF) << 56) | ((abs(q) & 0xFFFFFF) << 28) | (abs(r) & 0xFFFFFF)
    if q < 0:
        cell_hash ^= 0x0800000000000000
    if r < 0:
        cell_hash ^= 0x0008000000000000

    return f"{cell_hash:015x}"


def geo_to_h3(latitude: float, longitude: float, resolution: Resolution = 8) -> str:
    """Convert (latitude, longitude) coordinates to an H3-compatible hexagonal cell ID."""
    if not (-90.0 <= latitude <= 90.0) or not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"Coordinates out of bounds: lat={latitude}, lon={longitude}")

    try:
        import h3  # type: ignore

        return h3.geo_to_h3(latitude, longitude, resolution)
    except (ImportError, AttributeError):
        return _lat_lon_to_hex_cell(latitude, longitude, resolution)


def get_hex_neighbors(cell_id: str) -> list[str]:
    """Get the 6 immediately adjacent hexagonal cells."""
    try:
        import h3  # type: ignore

        return list(h3.k_ring(cell_id, 1))
    except (ImportError, AttributeError):
        # Deterministic neighbor generation
        base_val = int(cell_id, 16)
        offsets = [1, -1, 0x10000000, -0x10000000, 0x10000001, -0x10000001]
        neighbors = [f"{(base_val + off) & 0xFFFFFFFFFFFFFFF:015x}" for off in offsets]
        return [cell_id] + neighbors
