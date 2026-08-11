"""Extract (latitude, longitude) from common map URLs.

Used by the citizen + report flow as a convenience: a user can paste a
Google Maps / OpenStreetMap share link instead of typing coordinates.
The extractor is independent of ``civitas_geo`` — it only produces a
validated ``(lat, lon)`` pair. Once extracted, the coordinates flow
through the existing report submission path.

Supported formats:

- Google Maps ``/@lat,lon,zoom`` (e.g. ``https://www.google.com/maps/@28.6139,77.2090,15z``)
- Google Maps ``?q=lat,lon`` (e.g. ``https://maps.google.com/?q=28.6139,77.2090``)
- Google Maps ``?ll=lat,lon`` (alternative query)
- Google Maps ``/place/.../@lat,lon,zoom`` (place share links)
- OpenStreetMap ``?mlat=lat&mlon=lon`` (e.g. ``https://www.openstreetmap.org/?mlat=28.6139&mlon=77.2090#map=15/28.6139/77.2090``)
- OpenStreetMap ``?lat=...&lon=...`` (the simpler form)
- Plain ``lat,lon`` string (no scheme) — accepted as a fallback

URL-encoded query parameters are decoded before parsing. The output is
always a ``(latitude, longitude)`` tuple with both values in their
canonical ranges. Anything outside the ranges, or any URL that does
not match a known pattern, raises ``MapLinkError``.

The implementation is intentionally without third-party dependencies:
no ``urllib.parse`` beyond what's already in stdlib, no network calls,
no file I/O. Pure regex + float parsing.
"""

from __future__ import annotations

import re
from typing import Final
from urllib.parse import unquote, urlparse


# Canonical range (matches GeoPoint in civitas_geo and Pydantic Field bounds).
MIN_LAT: Final = -90.0
MAX_LAT: Final = 90.0
MIN_LON: Final = -180.0
MAX_LON: Final = 180.0


class MapLinkError(ValueError):
    """Raised when a URL cannot be parsed or its coordinates are invalid.

    Tests and the route translate this into a 422 (validation) response
    with code ``MAP_LINK_INVALID`` or ``MAP_LINK_OUT_OF_RANGE``.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Pattern catalogue
# ---------------------------------------------------------------------------

# Google Maps /@lat,lon,zoom or /place/.../@lat,lon,zoom
# Groups: 1=lat, 2=lon
_GMAPS_AT_RE = re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:[,/]|$)")

# Google Maps ?q=lat,lon or ?ll=lat,lon or ?center=lat,lon (URL-encoded or not)
# Groups: 1=key, 2=lat, 3=lon (URL-encoded forms)
#         4=key, 5=lat, 6=lon (comma-separated forms)
_GMAPS_QUERY_RE = re.compile(
    r"[?&](q|ll|center)=(-?\d+(?:\.\d+)?)%2C(-?\d+(?:\.\d+)?)"
    r"|[?&](q|ll|center)=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_coords(url: str) -> tuple[float, float]:
    """Parse a map URL and return ``(latitude, longitude)``.

    Raises:
        MapLinkError: ``MAP_LINK_INVALID`` if the URL is malformed or no
            known pattern matched; ``MAP_LINK_OUT_OF_RANGE`` if the
            extracted coordinates are outside their canonical ranges.
    """
    if not isinstance(url, str) or not url.strip():
        raise MapLinkError("MAP_LINK_INVALID", "url must be a non-empty string")

    raw = url.strip()
    decoded = unquote(raw)

    # Order matters: try the most specific patterns first.
    for parser in (
        _parse_plain_latlon,
        _parse_gmaps_at,
        _parse_gmaps_query,
        _parse_osm_query,
    ):
        try:
            coords = parser(decoded)
        except MapLinkError:
            continue
        if coords is not None:
            return _validate(*coords)

    raise MapLinkError(
        "MAP_LINK_INVALID",
        "url did not match a supported map-link format (google maps /@lat,lon, "
        "?q=lat,lon, ?ll=lat,lon, or openstreetmap ?mlat= / ?lon=)",
    )


# ---------------------------------------------------------------------------
# Pattern parsers
# ---------------------------------------------------------------------------


def _parse_plain_latlon(url: str) -> tuple[float, float] | None:
    """Plain "lat,lon" string with no scheme. e.g. "28.6139,77.2090"."""
    # Strip trailing junk like / or whitespace.
    candidate = url.strip().rstrip("/").strip()
    if "," not in candidate or " " in candidate or "/" in candidate or "?" in candidate:
        return None
    if not re.fullmatch(r"-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?", candidate):
        return None
    lat_s, lon_s = candidate.split(",", 1)
    try:
        return float(lat_s), float(lon_s)
    except ValueError as exc:
        raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


def _parse_gmaps_at(url: str) -> tuple[float, float] | None:
    """Google Maps /@lat,lon pattern. Most common share link."""
    m = _GMAPS_AT_RE.search(url)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except ValueError as exc:
        raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


def _parse_gmaps_query(url: str) -> tuple[float, float] | None:
    """Google Maps ?q=lat,lon or ?ll=lat,lon or ?center=lat,lon."""
    m = _GMAPS_QUERY_RE.search(url)
    if not m:
        return None
    # Either the %2C-encoded groups (1,2,3) or the comma-split groups (4,5,6).
    if m.group(1) is not None:
        # %2C path
        try:
            return float(m.group(2)), float(m.group(3))
        except ValueError as exc:
            raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")
    else:
        try:
            return float(m.group(5)), float(m.group(6))
        except ValueError as exc:
            raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


def _parse_osm_query(url: str) -> tuple[float, float] | None:
    """OpenStreetMap ?mlat / ?mlon or ?lat / ?lon.

    Looks for the canonical pair with the *m prefix first, then falls
    back to the bare pair. Both params must be present and parseable.
    """
    parsed = urlparse(url)
    if not parsed.query and not parsed.fragment:
        return None
    # URL params and fragment params both matter for OSM share links.
    bag: dict[str, str] = {}
    for source in (parsed.query, parsed.fragment):
        for part in source.split("&"):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            bag[k.lower()] = unquote(v)

    lat = bag.get("mlat") or bag.get("lat")
    lon = bag.get("mlon") or bag.get("lon")
    if lat is None or lon is None:
        return None
    try:
        return float(lat), float(lon)
    except ValueError as exc:
        raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _validate(latitude: float, longitude: float) -> tuple[float, float]:
    """Confirm both coordinates are in canonical range."""
    if not (MIN_LAT <= latitude <= MAX_LAT):
        raise MapLinkError(
            "MAP_LINK_OUT_OF_RANGE",
            f"latitude {latitude} outside [{MIN_LAT}, {MAX_LAT}]",
        )
    if not (MIN_LON <= longitude <= MAX_LON):
        raise MapLinkError(
            "MAP_LINK_OUT_OF_RANGE",
            f"longitude {longitude} outside [{MIN_LON}, {MAX_LON}]",
        )
    return latitude, longitude
