"""Duplicate clustering: union-find connected components over scored pairs.

Clustering groups reports into one real-world incident when the pairwise
composite evidence exceeds the threshold. The representative report is the
one with the strongest evidence (most media, richest description, latest
submission) so work orders can be anchored on the best observation.
"""

from __future__ import annotations

from dataclasses import dataclass

from civitas_duplicates.contracts import IncidentCluster, ReportLike
from civitas_duplicates.geo_features import gps_distance_m
from civitas_duplicates.similarity import ScoringConfig


@dataclass(frozen=True)
class ScoredPair:
    """A scored report pair with its explainable features."""

    a: str
    b: str
    score: float
    distance_m: float


class UnionFind:
    def __init__(self, ids: list[str]) -> None:
        self.parent = {i: i for i in ids}
        self.rank = {i: 0 for i in ids}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x: str, y: str) -> None:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

    def components(self) -> list[list[str]]:
        groups: dict[str, list[str]] = {}
        for i in self.parent:
            groups.setdefault(self.find(i), []).append(i)
        return list(groups.values())


def evidence_strength(report: ReportLike) -> float:
    """Deterministic evidence heuristic used only to pick representatives."""
    strength = 0.0
    strength += min(report.media_count, 4) * 1.5
    strength += min(len(report.description) / 200.0, 1.0)
    if report.image_embedding is not None:
        strength += 1.0
    if report.text_embedding is not None:
        strength += 0.5
    if report.landmark_ids:
        strength += 0.5
    return strength


def _span_m(ids: list[str], positions: dict[str, tuple[float, float]]) -> float:
    """Maximum pairwise GPS span within a cluster (O(n^2), n is cluster-sized)."""
    if len(ids) < 2:
        return 0.0
    span = 0.0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            d = gps_distance_m(
                positions[ids[i]][0], positions[ids[i]][1],
                positions[ids[j]][0], positions[ids[j]][1],
            )
            span = max(span, d)
    return span


def cluster_reports(
    reports: list[ReportLike],
    scored_pairs: list[ScoredPair],
    cfg: ScoringConfig | None = None,
    cluster_id_start: int = 1,
) -> list[IncidentCluster]:
    """Group reports into incident clusters from scored pairs.

    Edges above the composite threshold form connected components. Clusters
    with member_count == 1 are isolated reports (kept for caller symmetry).

    Phase 5: clusters get the product ID scheme CL-{n:03d} (e.g. CL-018),
    assigned deterministically in output order (largest cluster first). The
    counter starts at `cluster_id_start`; a production registry would persist
    it so IDs never collide across batches.
    """
    cfg = cfg or ScoringConfig()
    if cluster_id_start < 1:
        raise ValueError("cluster_id_start must be >= 1")
    if not reports:
        return []
    report_ids = [r.report_id for r in reports]
    pair_index = {(p.a, p.b): p for p in scored_pairs}
    uf = UnionFind(report_ids)
    for p in scored_pairs:
        if p.score >= cfg.duplicate_threshold:
            uf.union(p.a, p.b)

    positions = {r.report_id: (r.latitude, r.longitude) for r in reports}
    evidence = {r.report_id: evidence_strength(r) for r in reports}

    clusters: list[IncidentCluster] = []
    for comp in uf.components():
        comp_sorted = sorted(comp)
        scores: list[float] = []
        for i in range(len(comp_sorted)):
            for j in range(i + 1, len(comp_sorted)):
                pair = pair_index.get((comp_sorted[i], comp_sorted[j]))
                if pair is not None:
                    scores.append(pair.score)
        mean = (sum(scores) / len(scores)) if scores else 0.0
        span = _span_m(comp, positions)
        representative = max(comp, key=lambda rid: (evidence.get(rid, 0.0), rid))
        clusters.append(
            IncidentCluster(
                cluster_id=f"CL-{len(clusters) + cluster_id_start:03d}",
                report_ids=comp,
                representative_report_id=representative,
                member_count=len(comp),
                mean_pairwise_score=round(mean, 4),
                span_m=round(span, 1),
                basis=[
                    f"{len(comp)} report(s); edges above composite threshold "
                    f"{cfg.duplicate_threshold:.2f}",
                    f"representative {representative} chosen by evidence strength",
                ],
            )
        )
    clusters.sort(key=lambda c: (-c.member_count, c.cluster_id))
    return clusters