"""Phase 8: resolution-verification model — the second ML moment.

The first ML moment (Phases 3-7) understands the incident: vision, duplicate
detection, severity, priority. After the municipality acts, the second ML
moment verifies the outcome: the model compares the BEFORE photo evidence
with the AFTER photo evidence and answers one of four:

- RESOLVED          every hazard signal in the BEFORE evidence is gone;
- PARTIALLY RESOLVED some signals are gone but a residual remains (e.g. the
                    water is no longer flowing but standing water remains);
- UNVERIFIABLE      the comparison cannot be made (media rejected by the
                    quality gate, or the BEFORE carries no measurable
                    hazard to verify);
- CONFLICTING       the AFTER evidence contradicts a resolution: the hazard
                    is unchanged or worse, or a different hazard is now
                    observable at the site.

The model is deterministic and every reason cites the evidence it saw —
same house style as `SeverityModel` and `PriorityModel`. Quantified
gradients exist only for water damage (the `water_coverage` pixel
measurement); the other four categories are binary presence/absence, which
is a recorded limitation, not a hidden assumption.

Guard order (worst wins): unusable media -> UNVERIFIABLE (fail fast, never
guess); different hazard observable -> CONFLICTING; then tracks per hazard
signal present in the BEFORE: unchanged or worsened -> CONFLICTING;
reduced-but-present -> PARTIALLY RESOLVED; all gone -> RESOLVED.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from civitas_resolution.evidence import (
    STANDING_WATER_MARKER,
    WATER_FLOW_MARKERS,
    ResolutionEvidence,
)

# Mirrors the vision evidence rule threshold ("standing water" requires a
# blue-dominant smooth-region share >= 0.20): below it no standing water is
# observable, so the hazard signal counts as resolved.
STANDING_WATER_EVIDENCE_MIN = 0.20

# The AFTER coverage is only read as "worse" when it clearly grew (10%
# margin); anything less is residual water still present (partial).
COVERAGE_GROWTH_CONFLICT_RATIO = 1.10

# Single-hazard categories with no quantified residual: one observable
# marker each, presence in AFTER means the hazard is still there.
CATEGORY_HAZARD_MARKERS: dict[str, tuple[str, ...]] = {
    "pothole_road_damage": ("visible road cavity (pothole) with broken surface",),
    "garbage_overflow": ("mixed-color waste pile (scattered debris)",),
    "broken_streetlight": ("dark scene with a localized bright bulb region",),
    "fallen_tree": ("fallen trunk/blockage spanning the road",),
}

Outcome = Literal["resolved", "partial", "unverifiable", "conflicting"]
ReasonStatus = Literal["resolved", "partial", "unchanged", "worsened", "rejected"]

DISPLAY_LABELS: dict[str, str] = {
    "resolved": "RESOLVED",
    "partial": "PARTIALLY RESOLVED",
    "unverifiable": "UNVERIFIABLE",
    "conflicting": "CONFLICTING",
}


def outcome_label(outcome: Outcome) -> str:
    """Human-readable label for an outcome ('partially resolved', ...)."""
    return DISPLAY_LABELS[outcome]


class ResolutionReason(BaseModel):
    """One signal verdict with the evidence it saw."""

    factor: str
    status: ReasonStatus
    evidence: str


class ResolutionVerdict(BaseModel):
    """The model's answer for one before/after pair, fully explainable.

    `confidence` is a computed quantity, never curated: alignment between
    the tracks and the verdict, weighted by each track's margin (how far
    its measurement is from flipping) and compressed by signal richness,
    so a single binary signal can never reach high confidence.
    """

    incident_id: str
    outcome: Outcome
    confidence: float = Field(ge=0.0, le=1.0)
    resolved_signals: int = Field(ge=0)
    total_signals: int = Field(ge=0)
    reasons: list[ResolutionReason]
    basis: list[str]


class ResolutionModel:
    """Deterministic before/after comparison; every verdict is explainable."""

    model_version = "resolution-model-v1"

    # Per-track probative weight (relative evidence strength); weights of
    # the tracks present are renormalized to 1.0 before alignment.
    TRACK_WEIGHTS: dict[str, float] = {
        "active water flow": 0.55,
        "standing water / coverage": 0.30,
        "hazard evidence": 0.15,
    }

    def assess(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionVerdict:
        basis = [
            f"{self.model_version}: {before.stage} vs {after.stage} evidence comparison",
            "signals: active water flow, standing-water coverage, category hazard markers",
        ]

        guard = self._media_guard(before, after)
        if guard is not None:
            return self._verdict(before, "unverifiable", [guard], 0, 0, basis)

        mismatch = self._category_mismatch_reason(before, after)
        if mismatch is not None:
            return self._verdict(before, "conflicting", [mismatch], 0, 0, basis)

        reasons = self._signal_tracks(before, after)
        if not reasons:
            return self._verdict(
                before,
                "unverifiable",
                [ResolutionReason(
                    factor="verifiability",
                    status="rejected",
                    evidence=(
                        "before evidence carries no measurable hazard to verify "
                        f"(category {before.primary_category or 'unknown'}, coverage "
                        f"{before.water_coverage:.2f}, no hazard markers)"
                    ),
                )],
                0, 0, basis,
            )

        statuses = [r.status for r in reasons]
        if any(s in ("unchanged", "worsened") for s in statuses):
            outcome: Outcome = "conflicting"
        elif any(s == "partial" for s in statuses):
            outcome = "partial"
        else:
            outcome = "resolved"
        resolved = sum(1 for r in reasons if r.status == "resolved")
        return self._verdict(
            before, outcome, reasons, resolved, len(reasons), basis,
            confidence=self._confidence(outcome, reasons, before, after),
        )

    def _confidence(
        self,
        outcome: Outcome,
        reasons: list[ResolutionReason],
        before: ResolutionEvidence,
        after: ResolutionEvidence,
    ) -> float:
        """Computed confidence, never curated.

        confidence = alignment x margin-mean x richness, where:
        - alignment: weight share of tracks supporting the verdict
          (supporting sets: RESOLVED -> resolved; PARTIAL -> resolved OR
          partial, both mean "in progress"; CONFLICTING -> unchanged OR
          worsened);
        - margin: how far each track's measurement is from flipping to
          another verdict (binary tracks: 1.0 when decisive, 0.0 when the
          hazard is at full strength; the standing track measures distance
          from the growth-conflict boundary, and distance below the 0.20
          observable minimum when resolved);
        - richness: n/(n+1), so a single binary signal can never reach
          high confidence (cap 0.75 today with two water signals).
        """
        if outcome == "unverifiable":
            return 0.0
        supporting_sets: dict[Outcome, set[str]] = {
            "resolved": {"resolved"},
            "partial": {"resolved", "partial"},
            "conflicting": {"unchanged", "worsened"},
            "unverifiable": set(),
        }
        weights = self.TRACK_WEIGHTS
        total = sum(weights.get(r.factor, 0.1) for r in reasons)
        aligned = sum(
            weights.get(r.factor, 0.1)
            for r in reasons
            if r.status in supporting_sets[outcome]
        )
        margins = [self._track_margin(r, before, after) for r in reasons]
        n = len(reasons)
        margin_mean = sum(margins) / max(n, 1)
        richness = n / (n + 1)
        return round(min(max((aligned / total) if total else 0.0, 0.0), 1.0) * margin_mean * richness, 2)

    def _track_margin(
        self, reason: ResolutionReason, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> float:
        factor = reason.factor
        if factor == "active water flow":
            return 1.0 if reason.status == "resolved" else 0.0
        if factor == "standing water / coverage":
            boundary = before.water_coverage * COVERAGE_GROWTH_CONFLICT_RATIO
            if reason.status == "resolved":
                if before.water_coverage <= 0.0:
                    return 1.0
                below = (STANDING_WATER_EVIDENCE_MIN - after.water_coverage) / STANDING_WATER_EVIDENCE_MIN
                return float(min(max(below, 0.0), 1.0))
            if reason.status == "partial":
                if boundary <= before.water_coverage:
                    return 1.0
                progress = (boundary - after.water_coverage) / (boundary - before.water_coverage)
                return float(min(max(1.0 - progress, 0.0), 1.0))
            return 0.0
        return 1.0 if reason.status == "resolved" else 0.0

    def _media_guard(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionReason | None:
        for evidence in (before, after):
            if not evidence.media_usable:
                evidence_txt = "; ".join(evidence.rejection_basis)
                evidence_txt = evidence_txt or "quality gate rejected the media"
                return ResolutionReason(
                    factor=f"{evidence.stage} media",
                    status="rejected",
                    evidence=f"{evidence.source}: {evidence_txt}",
                )
        return None

    def _category_mismatch_reason(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionReason | None:
        if not (before.primary_category and after.primary_category):
            return None
        if before.primary_category == after.primary_category:
            return None
        if not after.observable_evidence:
            return None
        return ResolutionReason(
            factor="hazard type",
            status="unchanged",
            evidence=(
                f"after image shows a different hazard ({after.primary_category}, "
                f"evidence: {after.observable_evidence}) while the before image showed "
                f"{before.primary_category}; the reported hazard cannot be confirmed resolved"
            ),
        )

    def _signal_tracks(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> list[ResolutionReason]:
        reasons: list[ResolutionReason] = []
        if before.active_water_flow:
            reasons.append(self._flow_track(before, after))
        standing_before = (
            before.water_coverage >= STANDING_WATER_EVIDENCE_MIN
            or STANDING_WATER_MARKER in before.observable_evidence
        )
        if standing_before:
            reasons.append(self._standing_track(before, after))
        markers = CATEGORY_HAZARD_MARKERS.get(before.primary_category or "")
        if markers:
            reasons.append(self._marker_track(before, after))
        return reasons

    def _flow_track(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionReason:
        if after.active_water_flow:
            return ResolutionReason(
                factor="active water flow", status="unchanged",
                evidence=(
                    f"before: flow observed ({WATER_FLOW_MARKERS[0]}); "
                    "after: flow still observable — the leak keeps running"
                ),
            )
        return ResolutionReason(
            factor="active water flow", status="resolved",
            evidence=(
                f"before: flow observed ({WATER_FLOW_MARKERS[0]}); "
                "after: no active water flow detected"
            ),
        )

    def _standing_track(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionReason:
        after_present = (
            after.water_coverage >= STANDING_WATER_EVIDENCE_MIN
            or STANDING_WATER_MARKER in after.observable_evidence
        )
        if not after_present:
            return ResolutionReason(
                factor="standing water / coverage", status="resolved",
                evidence=(
                    f"before coverage {before.water_coverage:.2f}; after: no standing water "
                    f"(coverage {after.water_coverage:.2f}) and no standing-water evidence"
                ),
            )
        if after.water_coverage > before.water_coverage * COVERAGE_GROWTH_CONFLICT_RATIO:
            return ResolutionReason(
                factor="standing water / coverage", status="worsened",
                evidence=(
                    f"coverage grew from {before.water_coverage:.2f} to "
                    f"{after.water_coverage:.2f} (>{COVERAGE_GROWTH_CONFLICT_RATIO}x) — "
                    "water damage increased, not decreased"
                ),
            )
        return ResolutionReason(
            factor="standing water / coverage", status="partial",
            evidence=(
                f"before coverage {before.water_coverage:.2f}; after: standing water remains "
                f"(coverage {after.water_coverage:.2f}, evidence: {STANDING_WATER_MARKER})"
            ),
        )

    def _marker_track(
        self, before: ResolutionEvidence, after: ResolutionEvidence
    ) -> ResolutionReason:
        markers = CATEGORY_HAZARD_MARKERS[before.primary_category or ""]
        remaining = [m for m in after.observable_evidence if m in markers]
        if remaining:
            return ResolutionReason(
                factor="hazard evidence", status="unchanged",
                evidence=(
                    f"the reported hazard ({remaining[0]}) is still observable "
                    "in the after image"
                ),
            )
        return ResolutionReason(
            factor="hazard evidence", status="resolved",
            evidence=(
                f"no evidence of the reported hazard ({markers[0]}) "
                "remains in the after image"
            ),
        )

    def _verdict(
        self,
        before: ResolutionEvidence,
        outcome: Outcome,
        reasons: list[ResolutionReason],
        resolved: int,
        total: int,
        basis: list[str],
        confidence: float = 0.0,
    ) -> ResolutionVerdict:
        return ResolutionVerdict(
            incident_id=before.incident_id,
            outcome=outcome,
            confidence=confidence,
            resolved_signals=resolved,
            total_signals=total,
            reasons=reasons,
            basis=basis,
        )