"""Tests for the map-link extraction utility.

Covers:
- Google Maps /@lat,lon,...   (the most common share link)
- Google Maps ?q=lat,lon
- Google Maps ?ll=lat,lon
- Google Maps /place/.../@lat,lon,...
- Google Maps with URL-encoded query (%2C)
- OpenStreetMap ?mlat / ?mlon
- OpenStreetMap ?lat / ?lon   (bare form)
- OpenStreetMap with coords in the fragment (#map=15/lat/lon)
- Plain "lat,lon" string with no scheme
- Malformed URL  -> 422 MAP_LINK_INVALID
- Out-of-range   -> 422 MAP_LINK_OUT_OF_RANGE
- Unsupported URL -> 422 MAP_LINK_INVALID
- Empty / missing payload.url -> 422 VALIDATION_ERROR
- Integration: extracted coords fed straight into POST /api/v1/reports
"""

from __future__ import annotations

import jwt as pyjwt
from fastapi.testclient import TestClient

from civitas_api.main import app


GMAPS_AT = "https://www.google.com/maps/@28.6139,77.2090,15z"
GMAPS_Q = "https://maps.google.com/?q=28.6139,77.2090"
GMAPS_LL = "https://maps.google.com/?ll=28.6139,77.2090"
GMAPS_PLACE = "https://www.google.com/maps/place/Sunrise+School/@28.6139,77.2090,17z"
GMAPS_ENCODED = "https://maps.google.com/?q=28.6139%2C77.2090"
OSM_M = "https://www.openstreetmap.org/?mlat=28.6139&mlon=77.2090#map=15/28.6139/77.2090"
OSM_BARE = "https://www.openstreetmap.org/?lat=28.6139&lon=77.2090"
PLAIN = "28.6139,77.2090"


# ---------------------------------------------------------------------------
# Unit tests for the helper (no HTTP, pure logic)
# ---------------------------------------------------------------------------


def _extract(url: str):
    """Import the helper directly so we can test parse outcomes without
    running the HTTP layer."""
    from civitas_api.operations.map_link import extract_coords
    return extract_coords(url)


def test_gmaps_at_pattern() -> None:
    assert _extract(GMAPS_AT) == (28.6139, 77.2090)


def test_gmaps_q_pattern() -> None:
    assert _extract(GMAPS_Q) == (28.6139, 77.2090)


def test_gmaps_ll_pattern() -> None:
    assert _extract(GMAPS_LL) == (28.6139, 77.2090)


def test_gmaps_place_pattern() -> None:
    assert _extract(GMAPS_PLACE) == (28.6139, 77.2090)


def test_gmaps_url_encoded_query() -> None:
    assert _extract(GMAPS_ENCODED) == (28.6139, 77.2090)


def test_osm_mlat_mlon_pattern() -> None:
    assert _extract(OSM_M) == (28.6139, 77.2090)


def test_osm_lat_lon_pattern() -> None:
    assert _extract(OSM_BARE) == (28.6139, 77.2090)


def test_plain_latlon_string() -> None:
    assert _extract(PLAIN) == (28.6139, 77.2090)


def test_negative_coords() -> None:
    # Sao Paulo example
    assert _extract("https://www.google.com/maps/@-23.5505,-46.6333,12z") == (
        -23.5505,
        -46.6333,
    )


def test_zone_padding_after_coords() -> None:
    # /@lat,lon,zoomz (zoom suffix with 'z' character)
    assert _extract("https://www.google.com/maps/@28.6139,77.2090,15z/data=!3m1!4b1") == (
        28.6139,
        77.2090,
    )


def test_empty_string_raises() -> None:
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract("")
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_INVALID"
    else:
        raise AssertionError("expected MapLinkError")


def test_malformed_url_raises() -> None:
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract("https://example.com/no-coords-here")
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_INVALID"
    else:
        raise AssertionError("expected MapLinkError")


def test_out_of_range_latitude_raises() -> None:
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract("https://maps.google.com/?q=999,77.2090")
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_OUT_OF_RANGE"
        assert "latitude" in exc.message
    else:
        raise AssertionError("expected MapLinkError")


def test_out_of_range_longitude_raises() -> None:
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract("https://maps.google.com/?q=28.6139,999")
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_OUT_OF_RANGE"
        assert "longitude" in exc.message
    else:
        raise AssertionError("expected MapLinkError")


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


def _client() -> TestClient:
    return TestClient(app)


def test_endpoint_returns_google_maps_at() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": GMAPS_AT})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["latitude"] == 28.6139
    assert data["longitude"] == 77.2090
    assert data["url"] == GMAPS_AT


def test_endpoint_returns_google_maps_q() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": GMAPS_Q})
    assert r.status_code == 200
    assert r.json()["data"]["latitude"] == 28.6139


def test_endpoint_returns_osm() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": OSM_M})
    assert r.status_code == 200
    assert r.json()["data"]["longitude"] == 77.2090


def test_endpoint_returns_url_encoded() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": GMAPS_ENCODED})
    assert r.status_code == 200
    assert r.json()["data"]["latitude"] == 28.6139


def test_endpoint_rejects_malformed_url() -> None:
    r = _client().post(
        "/api/v1/map-extract", json={"url": "https://example.com/no-coords"}
    )
    assert r.status_code == 422
    body = r.json()
    assert body["detail"]["code"] == "MAP_LINK_INVALID"


def test_endpoint_rejects_out_of_range() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": "https://maps.google.com/?q=999,999"})
    assert r.status_code == 422
    body = r.json()
    assert body["detail"]["code"] == "MAP_LINK_OUT_OF_RANGE"


def test_endpoint_rejects_unsupported_format() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": "https://foo.bar/xxx"})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "MAP_LINK_INVALID"


def test_endpoint_rejects_empty_url() -> None:
    r = _client().post("/api/v1/map-extract", json={"url": ""})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_endpoint_rejects_missing_url_field() -> None:
    r = _client().post("/api/v1/map-extract", json={})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "VALIDATION_ERROR"


def test_endpoint_is_open_no_auth_required() -> None:
    """No Authorization header — must still succeed (utility endpoint)."""
    r = _client().post("/api/v1/map-extract", json={"url": GMAPS_AT})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Integration: extract coords then submit a report with them
# ---------------------------------------------------------------------------


def _citizen_header() -> dict[str, str]:
    tok = pyjwt.encode(
        {"sub": "citizen-1", "role": "citizen"},
        "test-secret-not-used-in-dev-mode",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {tok}"}


def test_extracted_coords_feed_into_report_submission() -> None:
    """End-to-end: extract coords from a Google Maps URL, then submit a
    report using those exact coordinates. The same flow as a citizen
    pasting a map link in the UI."""
    client = _client()

    # Step 1: extract coords from a map URL
    r1 = client.post("/api/v1/map-extract", json={"url": GMAPS_AT})
    assert r1.status_code == 200
    lat = r1.json()["data"]["latitude"]
    lon = r1.json()["data"]["longitude"]

    # Step 2: submit a report with those coords
    r2 = client.post(
        "/api/v1/reports",
        json={
            "description": "pot hole near the school gate",
            "location": {"latitude": lat, "longitude": lon},
            "citizen_selected_category": "pothole",
        },
        headers=_citizen_header(),
    )
    assert r2.status_code == 201, r2.text
    report = r2.json()["data"]
    assert report["latitude"] == lat
    assert report["longitude"] == lon
    assert report["report_id"].startswith("inc-")
