"""DuplicateDetector: end-to-end duplicate intelligence (Phase 5).

Pipeline for one report against the live incident store, or batch clustering
over all open reports:

1. embed text (cached) and reuse provided image embeddings,
2. spatial prefilter via PostGIS spatial_clusters / memory scan,
3. pairwise features: text + image + GPS + time + category (incl. related
   categories) + landmarks + transactional incident density,
4. composite decision per pair (explainable `DuplicateResult` with a ✓
   reasons checklist and per-feature contributions),
5. connected-component clustering into incident clusters with product IDs
   (CL-{n:03d}, e.g. CL-018).

Scoring uses the incident-anchored weights by default (Phase 4/5 semantics:
same incident is a physical-place-time claim, confirmed by language/pixels).
"""

from __future__ import annotations

from civitas_geo.landmarks import LandmarkIndex

from civitas_duplicates import geo_features, time_features
from civitas_duplicates.cluster import ScoredPair, cluster_reports
from civitas_duplicates.contracts import (
    DuplicateResult,
    IncidentCluster,
    PairFeatures,
    ReportLike,
)
from civitas_duplicates.embeddings import HashNgramEmbedder, TextEmbedder
from civitas_duplicates.signals import (
    category_relation,
    image_similarity,
    landmark_signal,
    text_similarity,
)
from civitas_duplicates.similarity import (
    INCIDENT_ANCHORED_WEIGHTS,
    ScoringConfig,
    composite_score,
    decide_duplicate,
    duplicate_reasons,
)

DENSITY_CELL_SIZE_M = 200.0


class DuplicateDetector:
    """Configurable duplicate detection engine (thread-safe for reads)."""

    def __init__(
        self,
        embedder: TextEmbedder | None = None,
        landmark_index: LandmarkIndex | None = None,
        config: ScoringConfig | None = None,
        max_candidates: int = 400,
        density_records: list[dict[str, object]] | None = None,
        density_cell_size_m: float = DENSITY_CELL_SIZE_M,
        cluster_id_start: int = 1,
    ) -> None:
        self.embedder = embedder or HashNgramEmbedder()
        self.landmarks = landmark_index or LandmarkIndex()
        self.config = config or ScoringConfig(weights=dict(INCIDENT_ANCHORED_WEIGHTS))
        self.max_candidates = max_candidates
        self._density_records = density_records or []
        self._density_cell_size_m = density_cell_size_m
        self.cluster_id_start = cluster_id_start

    # -- pair scoring ------------------------------------------------------

    def _text_embeddings(self, reports: list[ReportLike]) -> dict[str, list[float]]:
        cache: dict[str, list[float]] = {}
        for r in reports:
            if r.text_embedding is not None:
                cache[r.report_id] = r.text_embedding
            else:
                cache[r.report_id] = self.embedder.embed(r.description)
        return cache

    def _cell_density_map(self, reports: list[ReportLike]) -> dict[str, float]:
        """Normalized reports-per-cell density per report (Phase 5).

        Uses the transactional density history over the incident store
        (`density_records`): count of reports that landed in the same grid
        cell, capped at 50 (saturating similarity). Missing or failed
        aggregates record 0.0 — never fabricated.
        """
        out: dict[str, float] = {r.report_id: 0.0 for r in reports}
        if not self._density_records:
            return out
        try:
            from civitas_geo.aggregates import DensityAggregator, cell_id_for

            result = DensityAggregator(
                cell_size_m=self._density_cell_size_m
            ).reports_per_cell(self._density_records)
            by_cell = {c.cell_id: c.report_count for c in result.cells}
        except Exception:  # noqa: BLE001 - density is best-effort context evidence
            return out
        for r in reports:
            count = by_cell.get(
                cell_id_for(r.latitude, r.longitude, self._density_cell_size_m), 0
            )
            out[r.report_id] = min(1.0, count / 50.0)
        return out

    def pair_features(
        self,
        a: ReportLike,
        b: ReportLike,
        text_cache: dict[str, list[float]],
        cell_density: dict[str, float] | None = None,
    ) -> PairFeatures:
        text_sim = text_similarity(
            a.description,
            b.description,
            self.embedder,
            cached_a=text_cache.get(a.report_id),
            cached_b=text_cache.get(b.report_id),
        )
        img_sim = image_similarity(a.image_embedding, b.image_embedding)
        cat_agr, cat_note = category_relation(a.category, b.category)
        gps_sim, gps_dist = geo_features.gps_similarity(
            a.latitude, a.longitude, b.latitude, b.longitude,
            sigma_m=self._gps_sigma(),
        )
        time_sim, time_delta_h = time_features.time_similarity(a.submitted_at, b.submitted_at)
        lm_sim = landmark_signal(
            a.latitude, a.longitude, a.landmark_ids,
            b.latitude, b.longitude, b.landmark_ids,
            self.landmarks,
            radius_m=self.config.landmark_radius_m,
        )
        if cell_density:
            density = (cell_density.get(a.report_id, 0.0) + cell_density.get(b.report_id, 0.0)) / 2.0
        else:
            density = 0.0
        return PairFeatures(
            text_similarity=round(text_sim, 4),
            image_similarity=round(img_sim, 4) if img_sim is not None else None,
            category_agreement=round(cat_agr, 4),
            gps_similarity=round(gps_sim, 4),
            gps_distance_m=round(gps_dist, 1),
            time_similarity=round(time_sim, 4),
            time_delta_h=round(time_delta_h, 2),
            landmark_similarity=round(lm_sim, 4),
            incident_density=round(density, 4),
            category_relation_note=cat_note,
        )

    def _gps_sigma(self) -> float:
        return 150.0

    def evaluate_pair(self, a: ReportLike, b: ReportLike) -> DuplicateResult:
        """Score one pair and decide duplication with full explanation."""
        text_cache = {a.report_id: a.text_embedding or self.embedder.embed(a.description),
                      b.report_id: b.text_embedding or self.embedder.embed(b.description)}
        density = self._cell_density_map([a, b])
        features = self.pair_features(a, b, text_cache, cell_density=density)
        is_dup, basis, requires_review = decide_duplicate(features, self.config)
        matched = b.report_id if is_dup else None
        return DuplicateResult(
            report_a=a.report_id,
            report_b=b.report_id,
            is_duplicate=is_dup,
            matched_incident_id=matched,
            score=round(composite_score(features, self.config), 4),
            feature_contributions=features.contributions(),
            decision_basis=basis,
            requires_review=requires_review,
            reasons=duplicate_reasons(features, self.config),
        )

    # -- batch clustering --------------------------------------------------

    def cluster(
        self,
        reports: list[ReportLike],
        spatial_prefilter: list[tuple[str, str]] | None = None,
    ) -> list[IncidentCluster]:
        """Batch clustering; optional pair prefilter from a spatial layer.

        spatial_prefilter: list of (report_id_a, report_id_b) pairs to
        evaluate (e.g. produced by PostGIS spatial_clusters). When omitted,
        all unique pairs reduced by the candidate cap are scored.

        Phase 5: clusters get product IDs CL-{n:03d} from an internal
        counter (starting at `cluster_id_start`).
        """
        if len(reports) < 2:
            return cluster_reports(
                reports, [], self.config, cluster_id_start=self.cluster_id_start
            )

        text_cache = self._text_embeddings(reports)
        cell_density = self._cell_density_map(reports)
        by_id = {r.report_id: r for r in reports}

        if spatial_prefilter:
            pairs = [(by_id[a], by_id[b]) for a, b in spatial_prefilter if a in by_id and b in by_id]
        else:
            prefiltered = self._spatially_plausible_pairs(reports)
            pairs = list(prefiltered)

        scored: list[ScoredPair] = []
        for a, b in pairs:
            features = self.pair_features(a, b, text_cache, cell_density=cell_density)
            score = composite_score(features, self.config)
            is_dup, _, _ = decide_duplicate(features, self.config)
            if is_dup:
                scored.append(
                    ScoredPair(
                        a=a.report_id,
                        b=b.report_id,
                        score=round(score, 4),
                        distance_m=features.gps_distance_m,
                    )
                )

        clusters = cluster_reports(
            reports, scored, self.config, cluster_id_start=self.cluster_id_start
        )
        return clusters

    def _spatially_plausible_pairs(self, reports: list[ReportLike]) -> list[tuple[ReportLike, ReportLike]]:
        """Reducer: keep pairs within a generous GPS radius (index-friendly)."""
        reports = sorted(reports, key=lambda r: r.latitude)
        out: list[tuple[ReportLike, ReportLike]] = []
        cap = self.max_candidates
        for a in reports:
            for b in reports:
                if b.report_id <= a.report_id:
                    continue
                d = geo_features.gps_distance_m(a.latitude, a.longitude, b.latitude, b.longitude)
                if d <= self.config.max_reasonable_distance_m:
                    out.append((a, b))
                    if len(out) >= cap:
                        return out
        return out

    # -- convenience: match one report against a set ------------------------

    def find_duplicate_of(
        self,
        report: ReportLike,
        candidates: list[ReportLike],
    ) -> DuplicateResult | None:
        """Best-match duplicate for a new report, or None when no candidate matches."""
        if not candidates:
            return None
        results: list[DuplicateResult] = []
        for c in candidates:
            results.append(self.evaluate_pair(report, c))
        matches = [r for r in results if r.is_duplicate]
        if not matches:
            return None
        matches.sort(key=lambda r: r.score, reverse=True)
        return matches[0]