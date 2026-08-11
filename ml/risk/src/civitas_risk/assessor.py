"""End-to-end severity/priority assessment composition.

Intake receipts: given a RiskContext (with ExposureContext from the
geospatial layer), produce both decision scores with shared provenance.
"""

from __future__ import annotations

from dataclasses import dataclass

from civitas_risk.contracts import PriorityResult, RiskContext, SeverityResult
from civitas_risk.priority import PriorityAssessor
from civitas_risk.severity import SeverityAssessor


@dataclass
class RiskAssessment:
    severity: SeverityResult
    priority: PriorityResult

    def summary(self) -> str:
        return (
            f"[{self.severity.level} severity {self.severity.score:.2f} | "
            f"{self.priority.tier} priority {self.priority.score:.2f}]"
        )


class RiskAssessor:
    """One-call severity + priority for an incident context."""

    def __init__(
        self,
        severity: SeverityAssessor | None = None,
        priority: PriorityAssessor | None = None,
    ) -> None:
        self.severity = severity or SeverityAssessor()
        self.priority = priority or PriorityAssessor()

    def assess(self, ctx: RiskContext) -> RiskAssessment:
        sev = self.severity.assess(ctx)
        pri = self.priority.assess(ctx, sev.score)
        return RiskAssessment(severity=sev, priority=pri)

    def load_ml_calibration(self, artifact_path: str, blend: float = 0.35) -> None:
        self.severity = SeverityAssessor.from_artifact(artifact_path, blend)