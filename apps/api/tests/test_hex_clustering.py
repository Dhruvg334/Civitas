"""Unit and integration tests for H3-compatible hexagonal spatial grid indexing."""

import pytest
from civitas_geo.hex_index import geo_to_h3, get_hex_neighbors
from civitas_api.operations.hex_clustering import calculate_hex_recurrence


def test_geo_to_h3_resolution_8_and_9():
    lat, lon = 20.29614, 85.82451
    cell_8 = geo_to_h3(lat, lon, 8)
    cell_9 = geo_to_h3(lat, lon, 9)

    assert isinstance(cell_8, str)
    assert len(cell_8) >= 15
    assert isinstance(cell_9, str)
    assert len(cell_9) >= 15
    assert cell_8 != cell_9  # Different resolutions produce distinct cells


def test_hex_neighbors():
    cell_id = geo_to_h3(28.6139, 77.2090, 8)
    neighbors = get_hex_neighbors(cell_id)
    assert len(neighbors) >= 6
    assert cell_id in neighbors


def test_geo_to_h3_out_of_bounds_validation():
    with pytest.raises(ValueError):
        geo_to_h3(95.0, 77.0, 8)  # Latitude > 90

    with pytest.raises(ValueError):
        geo_to_h3(28.0, 195.0, 8)  # Longitude > 180


def test_calculate_hex_recurrence():
    summary = calculate_hex_recurrence(20.29614, 85.82451, resolution=8, months_lookback=6)
    assert summary.resolution == 8
    assert isinstance(summary.cell_id, str)
    assert isinstance(summary.incident_count_6m, int)
    assert isinstance(summary.is_chronic_failure_zone, bool)
    assert summary.recurrence_velocity_per_month >= 0.0


def test_geo_to_h3_extreme_boundaries():
    coords = [
        (90.0, 0.0),
        (-90.0, 0.0),
        (0.0, 180.0),
        (0.0, -180.0),
        (0.0, 0.0),
    ]
    for lat, lon in coords:
        cell = geo_to_h3(lat, lon, 8)
        assert isinstance(cell, str)
        assert len(cell) >= 15
