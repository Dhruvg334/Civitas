"""Landmark grounding: lookup, containment and overlap.

Landmarks are observable, named places (schools, hospitals, junctions,
markets, parks, water bodies, metro stations, pathways). They anchor
duplicate detection ("both reports are at the school gate"), location
validation (snapping) and exposure reasoning (school/hospital proximity).
"""

from __future__ import annotations

from civitas_geo import distance as geo
from civitas_geo.models import GeoPoint, Landmark, LandmarkDistance

DEMO_LANDMARKS: list[Landmark] = [
    # Deterministic demo city landmarks for offline development and tests.
    # In production these come from the PostGIS landmark table (see README).
    Landmark(landmark_id="lm-school-01", name="Sunrise Public School", kind="school", latitude=28.6139, longitude=77.2090, radius_m=200),
    Landmark(landmark_id="lm-school-02", name="City Model High School", kind="school", latitude=28.6200, longitude=77.2190, radius_m=200),
    Landmark(landmark_id="lm-hosp-01", name="Central District Hospital", kind="hospital", latitude=28.6100, longitude=77.2050, radius_m=300),
    Landmark(landmark_id="lm-hosp-02", name="Mother Teresa Clinic", kind="hospital", latitude=28.6250, longitude=77.2150, radius_m=150),
    Landmark(landmark_id="lm-junction-01", name="Kingsway Junction", kind="junction", latitude=28.6160, longitude=77.2130, radius_m=80),
    Landmark(landmark_id="lm-junction-02", name="Riverside Cross", kind="junction", latitude=28.6090, longitude=77.2100, radius_m=80),
    Landmark(landmark_id="lm-market-01", name="Old Bazaar Market", kind="market", latitude=28.6120, longitude=77.2180, radius_m=150),
    Landmark(landmark_id="lm-park-01", name="Municipal Park", kind="park", latitude=28.6180, longitude=77.2070, radius_m=250),
    Landmark(landmark_id="lm-water-01", name="Yamuna Floodplain", kind="waterbody", latitude=28.6050, longitude=77.2300, radius_m=400),
    Landmark(landmark_id="lm-metro-01", name="Civic Centre Metro", kind="metro_station", latitude=28.6190, longitude=77.2165, radius_m=120),
    Landmark(landmark_id="lm-path-01", name="School Access Pathway", kind="pathway", latitude=28.6143, longitude=77.2098, radius_m=60),
]


class LandmarkIndex:
    """In-memory landmark index with per-kind sorted slices for fast lookup."""

    def __init__(self, landmarks: list[Landmark] | None = None) -> None:
        self.landmarks: list[Landmark] = list(landmarks or DEMO_LANDMARKS)
        self._sorted: dict[str, list[Landmark]] = {}
        for kind in ("school", "hospital", "junction", "market", "park", "waterbody", "metro_station", "pathway"):
            self._sorted[kind] = sorted(
                (lm for lm in self.landmarks if lm.kind == kind),
                key=lambda lm: lm.latitude,
            )

    def nearest(
        self,
        point: GeoPoint,
        kind: str | None = None,
        max_distance_m: float = 5_000.0,
    ) -> LandmarkDistance | None:
        """Nearest landmark of an optional kind within max_distance_m."""
        candidates = self._sorted.get(kind, []) if kind else self.landmarks
        if not candidates:
            if kind is not None and kind not in self._sorted:
                # Query for an unknown kind is a caller error; fold to all kinds.
                candidates = self.landmarks
            else:
                return None
        best: Landmark | None = None
        best_d = max_distance_m
        for lm in candidates:
            d = geo.haversine_m(point.latitude, point.longitude, lm.latitude, lm.longitude)
            if d <= best_d:
                best_d = d
                best = lm
        if best is None:
            return None
        return LandmarkDistance(landmark=best, distance_m=best_d)

    def nearest_by_kind(
        self, point: GeoPoint, kind: str, max_distance_m: float = 5_000.0
    ) -> LandmarkDistance | None:
        return self.nearest(point, kind=kind, max_distance_m=max_distance_m)

    def within(self, point: GeoPoint, kind: str | None = None, radius_m: float = 300.0) -> list[Landmark]:
        """All landmarks of a kind within radius_m."""
        pool = self._sorted.get(kind, self.landmarks) if kind else self.landmarks
        if not pool:
            return []
        return [
            lm
            for lm in pool
            if geo.haversine_m(point.latitude, point.longitude, lm.latitude, lm.longitude) <= radius_m
        ]

    def overlap(
        self,
        landmarks_a: list[Landmark],
        landmarks_b: list[Landmark],
        radius_m: float = 150.0,
    ) -> float:
        """Fraction of A's landmarks matched by any B landmark within radius_m.

        Returns a value in [0, 1]; 1 means every landmark of A is also found
        near a landmark of B.
        """
        if not landmarks_a or not landmarks_b:
            return 0.0
        matched = 0
        for la in landmarks_a:
            for lb in landmarks_b:
                if geo.haversine_m(la.latitude, la.longitude, lb.latitude, lb.longitude) <= radius_m:
                    matched += 1
                    break
        return matched / len(landmarks_a)

    def singleton(self, point: GeoPoint, radius_m: float = 150.0) -> list[Landmark]:
        """Landmarks contained by this point (used for containment checks)."""
        return self.within(point, radius_m=radius_m)


def landmark_signal_terms(name: str) -> set[str]:
    """Normalized keyword set extracted from a landmark name for overlap matching."""
    tokens = name.lower().replace("-", " ").split()
    stop = {"the", "of", "and", "city", "municipal", "central", "old", "new", "model"}
    return {t for t in tokens if t not in stop and len(t) > 2}