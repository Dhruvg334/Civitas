"""Extract (latitude, longitude) from common map URLs.

Used by the citizen + report flow as a convenience: a user can paste a
Google Maps / OpenStreetMap share link instead of typing coordinates.
The extractor is independent of ``civitas_geo`` — it only produces a
validated ``(lat, lon)`` pair. Once extracted, the coordinates flow
through the existing report submission path.

Supported formats:

* Google Maps ``/@lat,lon,zoom`` (e.g. ``https://www.google.com/maps/@28.6139,77.2090,15z``)
* Google Maps ``/place/.../@lat,lon,zoom`` (place share links)
* Google Maps ``?q=lat,lon`` (search-form share link)
* Google Maps ``?ll=lat,lon`` / ``?center=lat,lon`` (legacy / alternate)
* Google Maps ``data=!3d<lat>!4d<lon>`` — the actual **pin/place**
  coordinates embedded in the share blob. This is preferred over the
  ``/@lat,lon`` viewport-center coordinates, which can be kilometers
  away from the pinned location.
* OpenStreetMap ``?mlat=lat&mlon=lon`` (e.g. ``https://www.openstreetmap.org/?mlat=28.6139&mlon=77.2090#map=15/28.6139/77.2090``)
* OpenStreetMap ``?lat=...&lon=...`` (the simpler form)
* Plain ``lat,lon`` string (no scheme) — accepted as a fallback

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
from typing import Final, NamedTuple
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


# Where the coordinates came from. Useful for debugging and for callers
# that want to know whether they got the authoritative pin vs the
# camera-center fallback.
SOURCE_GMAPS_PIN = "gmaps_pin_data"      # !3d/!4d inside data= blob (most accurate)
SOURCE_GMAPS_AT = "gmaps_at"             # /@lat,lon,zoom viewport center
SOURCE_GMAPS_QUERY = "gmaps_query"       # ?q=, ?ll=, ?center= viewport center
SOURCE_OSM = "osm"                       # OpenStreetMap ?mlat/?mlon or ?lat/?lon
SOURCE_PLAIN = "plain"                   # bare "lat,lon" string

SOURCE_PRIORITY: Final[tuple[str, ...]] = (
    SOURCE_GMAPS_PIN,
    SOURCE_GMAPS_AT,
    SOURCE_GMAPS_QUERY,
    SOURCE_OSM,
    SOURCE_PLAIN,
)


class ExtractResult(NamedTuple):
    """Successful extraction result, with provenance.

    Use :func:`extract_coords` if you only need the (lat, lon) pair —
    this NamedTuple is for callers that also want to know which pattern
    matched.
    """

    latitude: float
    longitude: float
    source: str


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

# Google Maps share-link "data=" blob containing the actual pin coordinates.
#
# A typical share URL looks like:
#
#     https://www.google.com/maps/place/Eiffel+Tower/@48.8584,2.2945,15z\
#         /data=!3m1!4b1!3d48.8584!4d2.2945
#
# After URL-decoding, the ``data=`` blob is a sequence of segments
# separated by ``!``:
#
#     !3m1   !4b1   !3d48.8584   !4d2.2945
#
# Segments are typed by a 2-character code:
#   ``3d`` / ``4d`` — latitude / longitude of the *pinned* location.
#   ``3m1``        — view-mode toggle (always present).
#   ``4b1``        — base-map type (always present).
#
# The ``!3d<lat>!4d<lon>`` pair encodes the coordinates of the actual
# place/marker the link points to — *not* the map viewport center.
# When both are present (which is common for "share" links), they can
# differ by several kilometers; we prefer ``!3d/!4d``.
#
# This regex matches the pin pair anywhere in the URL (after decoding),
# including the URL-encoded form ``%213d<lat>%214d<lon>`` if anyone
# passed us a still-encoded URL by accident.
_GMAPS_PIN_RE = re.compile(
    r"(?:%21|!)3d(-?\d+(?:\.\d+)?)(?:%21|!)4d(-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_coords(url: str) -> tuple[float, float]:
    """Parse a map URL and return ``(latitude, longitude)``.

    This is the canonical (and API-stable) entry point — it returns
    only the coordinate pair. For callers that also need provenance
    (which pattern matched), use :func:`extract_coords_with_source`.

    Raises:
        MapLinkError: ``MAP_LINK_INVALID`` if the URL is malformed or no
            known pattern matched; ``MAP_LINK_OUT_OF_RANGE`` if the
            extracted coordinates are outside their canonical ranges.
    """
    result = extract_coords_with_source(url)
    return result.latitude, result.longitude


def extract_coords_with_source(url: str) -> ExtractResult:
    """Parse a map URL and return an :class:`ExtractResult` with provenance.

    The ``source`` field tells the caller which pattern won the
    priority race:

    * ``"gmaps_pin_data"`` — Google ``!3d/!4d`` pin in the data blob
      (the actual pinned place — most accurate)
    * ``"gmaps_at"`` — Google ``/@lat,lon,zoom`` (camera/viewport center)
    * ``"gmaps_query"`` — Google ``?q=`` / ``?ll=`` / ``?center=``
    * ``"osm"`` — OpenStreetMap ``?mlat`` / ``?mlon`` or ``?lat`` / ``?lon``
    * ``"plain"`` — bare ``lat,lon`` string

    Raises:
        MapLinkError: same as :func:`extract_coords`.
    """
    if not isinstance(url, str) or not url.strip():
        raise MapLinkError("MAP_LINK_INVALID", "url must be a non-empty string")

    raw = url.strip()
    decoded = unquote(raw)

    # Priority order: pin coordinates beat camera-center coordinates.
    # The pin is the actual place; the camera center is just where the
    # map happens to be pointed and can be kilometers away.
    for source, parser in (
        (SOURCE_GMAPS_PIN, _parse_gmaps_pin_data),
        (SOURCE_GMAPS_AT, _parse_gmaps_at),
        (SOURCE_GMAPS_QUERY, _parse_gmaps_query),
        (SOURCE_OSM, _parse_osm_query),
        (SOURCE_PLAIN, _parse_plain_latlon),
    ):
        try:
            coords = parser(decoded)
        except MapLinkError:
            continue
        if coords is not None:
            latitude, longitude = _validate(*coords)
            return ExtractResult(latitude, longitude, source)

    raise MapLinkError(
        "MAP_LINK_INVALID",
        "url did not match a supported map-link format (google maps "
        "data=!3d/!4d pin, /@lat,lon, ?q=lat,lon, ?ll=lat,lon, or "
        "openstreetmap ?mlat= / ?lon=)",
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


def _parse_gmaps_pin_data(url: str) -> tuple[float, float] | None:
    """Google Maps ``data=!3d<lat>!4d<lon>`` — actual pin coordinates.

    The share-link ``data=`` blob encodes several things; the two we
    care about are ``!3d<lat>`` (the place's latitude) and ``!4d<lon>``
    (the place's longitude). The blob always carries them as a pair,
    and the order is always ``!3d`` before ``!4d`` within a place block.

    Because the ``!`` separators are sometimes URL-encoded as ``%21``,
    and the whole ``data=`` value can itself be URL-encoded, we run
    the regex against the post-``unquote`` URL. ``_GMAPS_PIN_RE``
    accepts both ``!`` and ``%21`` separators, so an accidentally
    still-encoded input still matches.
    """
    m = _GMAPS_PIN_RE.search(url)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except ValueError as exc:
        raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


def _parse_gmaps_at(url: str) -> tuple[float, float] | None:
    """Google Maps ``/@lat,lon,zoom`` pattern — camera/viewport center.

    This is the *fallback* when no ``!3d/!4d`` pin is present. The
    ``/@lat,lon`` coordinates describe where the map is currently
    pointed, which is not always the same as the pinned place.
    """
    m = _GMAPS_AT_RE.search(url)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except ValueError as exc:
        raise MapLinkError("MAP_LINK_INVALID", f"could not parse coordinates: {exc}")


def _parse_gmaps_query(url: str) -> tuple[float, float] | None:
    """Google Maps ``?q=lat,lon`` or ``?ll=lat,lon`` or ``?center=lat,lon``."""
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
    """OpenStreetMap ``?mlat / ?mlon`` or ``?lat / ?lon``.

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