"""Location validation for citizen reports.

Validates coordinate structure, city coverage, plausibility and internal
consistency. Everything beyond the pure range checks is a labelled heuristic
(warning), never an asserted fact, so review stays easy.
"""

from __future__ import annotations

from civitas_geo import distance as geo
from civitas_geo.boundary import DEFAULT_BOUNDARY
from civitas_geo.landmarks import LandmarkIndex
from civitas_geo.models import (
    GeoPoint,
    LocationValidationResult,
    OperationalBoundary,
    PipelineGateDecision,
    Plausibility,
)

# Default operational bounding box (Civitas demo city). Overridable per city.
DEFAULT_CITY_BBOX: tuple[float, float, float, float] = (28.55, 77.15, 28.66, 77.27)

# A single-degree ocean mask for coarse plausibility. Expressed as
# (min_lat, max_lat, min_lon, max_lon) land-absent marine bands. Heuristic only:
# absence of a bad band does not prove "on land" without a geocoder.
_OCEAN_BANDS: list[tuple[float, float, float, float]] = []


class LocationValidator:
    """Composite location validator: structure, bounds, city, consistency."""

    def __init__(
        self,
        landmarks: LandmarkIndex | None = None,
        city_bbox: tuple[float, float, float, float] = DEFAULT_CITY_BBOX,
    ) -> None:
        self.landmarks = landmarks or LandmarkIndex()
        self.city_bbox = city_bbox

    def _in_city(self, p: GeoPoint) -> bool:
        min_lat, min_lon, max_lat, max_lon = self.city_bbox
        return min_lat <= p.latitude <= max_lat and min_lon <= p.longitude <= max_lon

    def _in_ocean_band(self, p: GeoPoint) -> bool:
        for min_lat, max_lat, min_lon, max_lon in _OCEAN_BANDS:
            if min_lat <= p.latitude <= max_lat and min_lon <= p.longitude <= max_lon:
                return True
        return False

    def validate(self, point: GeoPoint | dict[str, float]) -> LocationValidationResult:
        warnings: list[str] = []
        basis: list[str] = []

        try:
            point = GeoPoint.model_validate(point) if isinstance(point, dict) else point
        except Exception:
            return LocationValidationResult(
                point=GeoPoint(latitude=0.0, longitude=0.0),
                is_valid=False,
                plausibility="implausible",
                warnings=["Coordinates missing or malformed."],
                basis=["structure check"],
            )

        if point.latitude == 0.0 and point.longitude == 0.0:
            warnings.append("Exact (0, 0) coordinate is a common placeholder; verify source.")
            plausibility: Plausibility = "implausible"
            return LocationValidationResult(
                point=point,
                is_valid=False,
                plausibility=plausibility,
                warnings=warnings,
                basis=["placeholder heuristic"],
            )

        if not self._in_city(point):
            warnings.append(
                "Point is outside the operational city bounding box; treat as off-coverage."
            )
            plausibility = "implausible" if self._in_ocean_band(point) else "uncertain"
            return LocationValidationResult(
                point=point,
                is_valid=False,
                plausibility=plausibility,
                warnings=warnings,
                basis=["city bounding box check", "ocean band heuristic"],
            )

        plausibility = "plausible"
        if self._in_ocean_band(point):
            warnings.append("Point falls inside a known marine band (heuristic).")
            plausibility = "implausible"

        snap: GeoPoint | None = None
        nearest_lm = self.landmarks.nearest(point, max_distance_m=400.0)
        if nearest_lm is not None and nearest_lm.distance_m <= nearest_lm.landmark.radius_m:
            snap = GeoPoint(
                latitude=nearest_lm.landmark.latitude,
                longitude=nearest_lm.landmark.longitude,
                accuracy_m=point.accuracy_m,
            )
            warnings.append(
                f"Suggestion only: snapped to landmark '{nearest_lm.landmark.name}' "
                f"({nearest_lm.distance_m:.0f} m away). Confirm before use."
            )
            basis.append(f"landmark containment: {nearest_lm.landmark.landmark_id}")

        basis.append("within city bounding box")
        basis.append("structure/range checks passed")
        return LocationValidationResult(
            point=point,
            is_valid=True,
            plausibility=plausibility,
            warnings=warnings,
            suggested_snap=snap,
            basis=basis,
        )

    def compare_reports(self, a: GeoPoint, b: GeoPoint) -> list[str]:
        """Consistency warnings when two distinct reports share coordinates."""
        out: list[str] = []
        if a.latitude == b.latitude and a.longitude == b.longitude:
            out.append(
                "Identical coordinates across reports: repeated exact GPS may indicate "
                "copy-paste or spoofing rather than independent citizen readings."
            )
        elif geo.haversine_m(a.latitude, a.longitude, b.latitude, b.longitude) < 25.0:
            out.append("Coordinates within 25 m are plausibly the same physical spot.")
        return out


def gate_for_pipeline(
    point: GeoPoint | dict[str, float],
    boundary: OperationalBoundary | None = None,
    landmarks: LandmarkIndex | None = None,
) -> PipelineGateDecision:
    """Gate: is a report geographically plausible enough to enter the spatial
    pipeline (Phase 2)?

    The spatial stage must not receive missing, placeholder or off-coverage
    coordinates: those records go to a human-fix queue instead of candidate
    retrieval. "Uncertain but inside coverage" enters with warnings intact.
    """
    boundary = boundary or DEFAULT_BOUNDARY
    validator = LocationValidator(landmarks=landmarks, city_bbox=boundary.bbox)
    result = validator.validate(point)

    if result.is_valid:
        if result.plausibility == "implausible":
            return PipelineGateDecision(
                can_enter=False,
                reason="rejected_implausible",
                warnings=result.warnings,
                validation=result,
            )
        return PipelineGateDecision(
            can_enter=True,
            reason="approved",
            warnings=result.warnings,
            validation=result,
        )

    joined = " ".join(result.warnings).lower()
    if "missing or malformed" in joined:
        return PipelineGateDecision(
            can_enter=False,
            reason="rejected_malformed",
            warnings=result.warnings,
            validation=result,
        )
    if "placeholder" in joined:
        return PipelineGateDecision(
            can_enter=False,
            reason="rejected_placeholder",
            warnings=result.warnings,
            validation=result,
        )
    return PipelineGateDecision(
        can_enter=False,
        reason="rejected_out_of_coverage",
        warnings=result.warnings,
        validation=result,
    )