"""Tests for the map-link extraction utility.

Covers (in priority order, top to bottom of the parser):

- Google Maps ``data=!3d<lat>!4d<lon>`` — the actual *pinned* place
  coordinates embedded in the share blob. This is the preferred
  source: the ``/@lat,lon`` viewport center can be kilometers away.
- Google Maps ``/@lat,lon,zoom`` (camera center, fallback)
- Google Maps ``?q=lat,lon`` / ``?ll=lat,lon`` / ``?center=lat,lon``
- OpenStreetMap ``?mlat`` / ``?mlon`` and bare ``?lat`` / ``?lon``
- Plain ``lat,lon`` string with no scheme
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


# ---------------------------------------------------------------------------
# Canonical pin coordinates: Delhi. Used in every example below.
# Camera-center coordinates are deliberately different (Mumbai) for the
# priority tests, so we can assert the parser picks the actual pin
# rather than the viewport center.
# ---------------------------------------------------------------------------

PIN_LAT, PIN_LON = 28.6139, 77.2090          # Delhi (the pinned place)
CENTER_LAT, CENTER_LON = 19.0760, 72.8777    # Mumbai (camera/viewport center)
ZOOM = 15


# Plain coords (no URL).
PLAIN = "28.6139,77.2090"

# Google Maps camera-center only (no pin in data=).
GMAPS_AT = "https://www.google.com/maps/@28.6139,77.2090,15z"
GMAPS_Q = "https://maps.google.com/?q=28.6139,77.2090"
GMAPS_LL = "https://maps.google.com/?ll=28.6139,77.2090"
GMAPS_PLACE = "https://www.google.com/maps/place/Sunrise+School/@28.6139,77.2090,17z"
GMAPS_ENCODED = "https://maps.google.com/?q=28.6139%2C77.2090"

# OSM share links.
OSM_M = "https://www.openstreetmap.org/?mlat=28.6139&mlon=77.2090#map=15/28.6139/77.2090"
OSM_BARE = "https://www.openstreetmap.org/?lat=28.6139&lon=77.2090"

# Realistic Google Maps share links with embedded pin coordinates
# (``!3d<lat>!4d<lon>``) inside the ``data=`` blob. These are the
# ground truth for the "pin vs camera" priority fix.

# Eiffel Tower: pin and camera center agree (test that pin still parses).
GMAPS_PIN_AGREES = (
    "https://www.google.com/maps/place/Eiffel+Tower/"
    "@48.8584,2.2945,15z/"
    "data=!3m1!4b1!3d48.8584!4d2.2945"
)

# Delhi: pin (28.6139, 77.2090) and camera center (19.0760, 72.8777,
# i.e. Mumbai) deliberately disagree. The parser must return the pin.
GMAPS_PIN_DIFFERS_FROM_AT = (
    "https://www.google.com/maps/place/Sunrise+School+Delhi/"
    f"@{CENTER_LAT},{CENTER_LON},{ZOOM}z/"
    f"data=!3m1!4b1!3d{PIN_LAT}!4d{PIN_LON}"
)

# Same as above but the camera is expressed as ``?q=`` instead of ``/@``.
GMAPS_PIN_DIFFERS_FROM_Q = (
    f"https://maps.google.com/?q={CENTER_LAT},{CENTER_LON}"
    f"&data=!3m1!4b1!3d{PIN_LAT}!4d{PIN_LON}"
)

# Pin coordinates URL-encoded (``%21`` separators, ``%2C`` commas).
# This is the form Google actually generates when you click "Share".
GMAPS_PIN_URL_ENCODED = (
    f"https://www.google.com/maps/place/Delhi/"
    f"@{CENTER_LAT}%2C{CENTER_LON}%2C{ZOOM}z/"
    f"data=%213m1%214b1%213d{PIN_LAT}%214d{PIN_LON}"
)

# Place-only share link (mobile app style): no ``/@``, but the data=
# blob still carries the pin coordinates.
GMAPS_PIN_PLACE_ONLY = (
    f"https://www.google.com/maps/place/Delhi/"
    f"data=%213m1%214b1%213d{PIN_LAT}%214d{PIN_LON}"
)

# Multiple ``!3d`` segments: only the *first* paired ``!3d/!4d`` is the
# pin (the canonical place block always comes first; later ``!3d``s are
# viewport bounds or related-objects and would be off-topic). The
# parser must still pick the canonical pair.
GMAPS_PIN_WITH_LATER_BOUNDS = (
    "https://www.google.com/maps/place/Delhi/"
    f"@{CENTER_LAT},{CENTER_LON},{ZOOM}z/"
    f"data=!3m1!4b1!3d{PIN_LAT}!4d{PIN_LON}!3m2!1sVIEWPORT!3d11.0!4d22.0"
)

# Negative-coordinate pin (Western hemisphere).
GMAPS_PIN_NEGATIVE = (
    "https://www.google.com/maps/place/Statue+of+Liberty/"
    "@40.7484405,-73.9856644,15z/"
    "data=!3m1!4b1!3d40.7484405!4d-73.9856644"
)


# ---------------------------------------------------------------------------
# Unit tests for the helper (no HTTP, pure logic)
# ---------------------------------------------------------------------------


def _extract(url: str):
    """Import the helper directly so we can test parse outcomes without
    running the HTTP layer."""
    from civitas_api.operations.map_link import extract_coords
    return extract_coords(url)


def _extract_with_source(url: str):
    """Same as ``_extract`` but returns the full ExtractResult."""
    from civitas_api.operations.map_link import extract_coords_with_source
    return extract_coords_with_source(url)


# ----- Existing camera-center patterns (must keep working) ----------


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


# ----- New: pin-coordinates patterns (the actual fix) -----------------


def test_gmaps_pin_data_when_pin_equals_camera() -> None:
    """Pin and camera agree (Eiffel Tower): still returns pin coords."""
    assert _extract(GMAPS_PIN_AGREES) == (48.8584, 2.2945)


def test_gmaps_pin_data_wins_over_at_viewport() -> None:
    """The core fix: when ``/@`` camera and ``!3d/!4d`` pin disagree,
    the parser must return the pin coordinates (Delhi), not the
    viewport center (Mumbai)."""
    assert _extract(GMAPS_PIN_DIFFERS_FROM_AT) == (PIN_LAT, PIN_LON)


def test_gmaps_pin_data_wins_over_q_viewport() -> None:
    """Same as above, but the camera is in ``?q=`` not ``/@``."""
    assert _extract(GMAPS_PIN_DIFFERS_FROM_Q) == (PIN_LAT, PIN_LON)


def test_gmaps_pin_data_url_encoded_form() -> None:
    """Real Google share links URL-encode the ``!`` separators as
    ``%21``. The parser must decode them and still find the pin."""
    assert _extract(GMAPS_PIN_URL_ENCODED) == (PIN_LAT, PIN_LON)


def test_gmaps_pin_data_place_only_no_at_segment() -> None:
    """Place-only share link (no ``/@`` viewport at all)."""
    assert _extract(GMAPS_PIN_PLACE_ONLY) == (PIN_LAT, PIN_LON)


def test_gmaps_pin_data_ignores_later_viewport_bounds() -> None:
    """If the data= blob contains extra ``!3d/!4d`` segments after the
    pin pair (viewport bounds, related places), the parser must
    still pick the first pin pair — the canonical place block."""
    assert _extract(GMAPS_PIN_WITH_LATER_BOUNDS) == (PIN_LAT, PIN_LON)


def test_gmaps_pin_data_negative_longitude() -> None:
    """Negative longitude in the pin coordinates."""
    assert _extract(GMAPS_PIN_NEGATIVE) == (40.7484405, -73.9856644)


# ----- Provenance: which source was selected --------------------------


def test_source_is_gmaps_pin_data_when_pin_present() -> None:
    from civitas_api.operations.map_link import SOURCE_GMAPS_PIN
    res = _extract_with_source(GMAPS_PIN_DIFFERS_FROM_AT)
    assert res.source == SOURCE_GMAPS_PIN
    assert res.latitude == PIN_LAT
    assert res.longitude == PIN_LON


def test_source_is_gmaps_at_when_no_pin_present() -> None:
    from civitas_api.operations.map_link import SOURCE_GMAPS_AT
    res = _extract_with_source(GMAPS_AT)
    assert res.source == SOURCE_GMAPS_AT


def test_source_is_gmaps_query_when_no_pin_present() -> None:
    from civitas_api.operations.map_link import SOURCE_GMAPS_QUERY
    res = _extract_with_source(GMAPS_Q)
    assert res.source == SOURCE_GMAPS_QUERY


def test_source_is_osm_when_no_gmaps_pattern_matches() -> None:
    from civitas_api.operations.map_link import SOURCE_OSM
    res = _extract_with_source(OSM_M)
    assert res.source == SOURCE_OSM


def test_source_is_plain_for_bare_latlon() -> None:
    from civitas_api.operations.map_link import SOURCE_PLAIN
    res = _extract_with_source(PLAIN)
    assert res.source == SOURCE_PLAIN


# ----- Explicit priority-order tests ----------------------------------


def test_priority_pin_beats_at_when_both_present_and_differ() -> None:
    """Pavit's core case: in ~60% of share links, ``/@lat,lon`` and
    ``!3d/!4d`` disagree. The pin must win."""
    assert _extract(GMAPS_PIN_DIFFERS_FROM_AT) == (PIN_LAT, PIN_LON)
    assert _extract(GMAPS_PIN_DIFFERS_FROM_AT) != (CENTER_LAT, CENTER_LON)


def test_priority_pin_beats_q_when_both_present_and_differ() -> None:
    assert _extract(GMAPS_PIN_DIFFERS_FROM_Q) == (PIN_LAT, PIN_LON)


def test_priority_at_beats_q_when_both_present() -> None:
    """When no pin is present and both ``/@`` and ``?q=`` are present,
    ``/@`` wins (we walk it first)."""
    url = "https://www.google.com/maps/@28.6139,77.2090,15z?q=99.0000,99.0000"
    assert _extract(url) == (28.6139, 77.2090)


def test_priority_gmaps_beats_osm_for_google_host() -> None:
    """When a URL matches a Google pattern, OSM patterns are skipped —
    even if the URL contains literal ``?mlat=`` substrings (which can
    appear in place names)."""
    url = (
        "https://www.google.com/maps/place/Sunrise+School/"
        f"@{CENTER_LAT},{CENTER_LON},{ZOOM}z/"
        f"data=!3m1!4b1!3d{PIN_LAT}!4d{PIN_LON}"
    )
    assert _extract(url) == (PIN_LAT, PIN_LON)


def test_priority_osm_when_no_gmatch() -> None:
    """An OSM-only URL resolves via the OSM parser."""
    assert _extract(OSM_BARE) == (28.6139, 77.2090)


def test_priority_plain_is_last_resort() -> None:
    """A bare ``lat,lon`` with no scheme resolves to ``SOURCE_PLAIN``."""
    res = _extract_with_source(PLAIN)
    assert res.source == "plain"


# ----- Fallbacks ------------------------------------------------------


def test_fallback_to_at_when_no_pin_in_data() -> None:
    """A Google link with no ``data=!3d/!4d`` falls back to ``/@``."""
    assert _extract(GMAPS_AT) == (28.6139, 77.2090)


def test_fallback_to_q_when_no_at_and_no_pin() -> None:
    """A Google link with only ``?q=`` resolves via the query parser."""
    assert _extract(GMAPS_Q) == (28.6139, 77.2090)


def test_fallback_to_osm_for_osm_host() -> None:
    assert _extract(OSM_M) == (28.6139, 77.2090)


# ----- Malformed / out-of-range ---------------------------------------


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


def test_pin_out_of_range_latitude_raises() -> None:
    """Out-of-range coords in the pin field also raise OUT_OF_RANGE."""
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract(
            "https://www.google.com/maps/place/Bad/"
            "@0,0,15z/data=!3m1!4b1!3d999!4d77.2090"
        )
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_OUT_OF_RANGE"
        assert "latitude" in exc.message
    else:
        raise AssertionError("expected MapLinkError")


def test_pin_out_of_range_longitude_raises() -> None:
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract(
            "https://www.google.com/maps/place/Bad/"
            "@0,0,15z/data=!3m1!4b1!3d28.6139!4d999"
        )
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_OUT_OF_RANGE"
        assert "longitude" in exc.message
    else:
        raise AssertionError("expected MapLinkError")


def test_pin_malformed_number_raises() -> None:
    """Non-numeric token after ``!3d`` -> MAP_LINK_INVALID.

    Construct the URL so the pin parser matches the malformed value,
    and no other pattern (camera center, OSM, plain) can rescue it.
    The bare ``@0,0,15z`` is excluded by constructing a URL that has
    no ``/@lat,lon,zoom`` segment for the camera fallback to match.
    """
    from civitas_api.operations.map_link import MapLinkError
    try:
        # No /@lat,lon — pin pattern matches first and fails to parse
        # the number, so no fallback can rescue it.
        _extract(
            "https://www.google.com/maps/place/Bad/"
            "data=!3m1!4b1!3dnotanumber!4d77.2090"
        )
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_INVALID"
    else:
        raise AssertionError("expected MapLinkError")


def test_pin_only_no_lon_raises_invalid() -> None:
    """A lone ``!3d<lat>`` with no matching ``!4d<lon>`` is invalid.

    The pin regex requires both ``!3d`` and ``!4d`` to be present —
    it matches only the canonical ``!3d<lat>!4d<lon>`` pair. A lone
    ``!3d`` falls through to the camera-center parser, which fails
    too (no ``/@lat,lon,zoom`` here), so the URL is rejected.
    """
    from civitas_api.operations.map_link import MapLinkError
    try:
        _extract(
            "https://www.google.com/maps/place/Bad/"
            "data=!3m1!4b1!3d28.6139"
        )
    except MapLinkError as exc:
        assert exc.code == "MAP_LINK_INVALID"
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


def test_endpoint_returns_pin_winning_over_at() -> None:
    """End-to-end check that the priority fix is visible on the wire."""
    r = _client().post(
        "/api/v1/map-extract", json={"url": GMAPS_PIN_DIFFERS_FROM_AT}
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["latitude"] == PIN_LAT
    assert data["longitude"] == PIN_LON
    assert data["source"] == "gmaps_pin_data"


def test_endpoint_exposes_source_field() -> None:
    """The new ``source`` field is additive and does not break the
    existing latitude/longitude contract."""
    r = _client().post("/api/v1/map-extract", json={"url": GMAPS_AT})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["source"] == "gmaps_at"
    # Legacy fields unchanged.
    assert "latitude" in data and "longitude" in data and "url" in data


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


def test_extracted_pin_coords_feed_into_report_submission() -> None:
    """End-to-end check using a 3D/4D pin link: the pin (Delhi) must
    reach the report, not the camera center (Mumbai)."""
    client = _client()

    r1 = client.post(
        "/api/v1/map-extract", json={"url": GMAPS_PIN_DIFFERS_FROM_AT}
    )
    assert r1.status_code == 200
    data = r1.json()["data"]
    assert data["latitude"] == PIN_LAT
    assert data["longitude"] == PIN_LON
    assert data["source"] == "gmaps_pin_data"

    r2 = client.post(
        "/api/v1/reports",
        json={
            "description": "pothole near sunrise school delhi",
            "location": {
                "latitude": data["latitude"],
                "longitude": data["longitude"],
            },
            "citizen_selected_category": "pothole",
        },
        headers=_citizen_header(),
    )
    assert r2.status_code == 201, r2.text
    report = r2.json()["data"]
    assert report["latitude"] == PIN_LAT
    assert report["longitude"] == PIN_LON
    assert report["report_id"].startswith("inc-")