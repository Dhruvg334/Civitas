"""Municipal Contractor Performance & SLA Compliance Evaluation Engine.

Computes statutory SLA compliance percentages, Mean Time to Resolution (MTTR),
citizen dispute frequency, and composite performance rankings.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ContractorScorecard:
    contractor_id: str
    department: str
    total_assigned_jobs: int
    completed_jobs: int
    sla_compliant_jobs: int
    sla_compliance_rate_pct: float
    mean_time_to_resolution_hours: float
    dispute_count: int
    dispute_rate_pct: float
    composite_performance_score: float  # 0 to 100
    performance_tier: str  # "TIER_1_EXCELLENT", "TIER_2_GOOD", "TIER_3_UNDERPERFORMING"


def compute_contractor_scorecard(
    contractor_id: str,
    department: str,
    job_records: list[dict[str, Any]],
) -> ContractorScorecard:
    """Computes comprehensive performance scorecard for a municipal contractor/department."""
    if not job_records:
        return ContractorScorecard(
            contractor_id=contractor_id,
            department=department,
            total_assigned_jobs=0,
            completed_jobs=0,
            sla_compliant_jobs=0,
            sla_compliance_rate_pct=100.0,
            mean_time_to_resolution_hours=0.0,
            dispute_count=0,
            dispute_rate_pct=0.0,
            composite_performance_score=85.0,
            performance_tier="TIER_2_GOOD",
        )

    total = len(job_records)
    completed = 0
    sla_compliant = 0
    total_duration_hours = 0.0
    disputes = 0

    for job in job_records:
        is_done = job.get("status") in ("resolved", "closed", "completed")
        if is_done:
            completed += 1
            dur = float(job.get("duration_hours", 12.0))
            sla_target = float(job.get("sla_target_hours", 24.0))
            total_duration_hours += dur

            if dur <= sla_target:
                sla_compliant += 1

        if job.get("is_disputed") or job.get("status") == "reopened_disputed":
            disputes += 1

    mttr = round(total_duration_hours / max(1, completed), 1) if completed > 0 else 0.0
    sla_pct = round((sla_compliant / max(1, completed)) * 100.0, 1) if completed > 0 else 100.0
    disp_pct = round((disputes / max(1, total)) * 100.0, 1)

    # Composite score formula: 50% SLA compliance + 30% Low Dispute + 20% Speed Factor
    speed_factor = max(0.0, min(100.0, 100.0 - (mttr * 1.5)))
    comp_score = round(
        0.50 * sla_pct + 0.30 * (100.0 - disp_pct) + 0.20 * speed_factor,
        1,
    )
    comp_score = max(0.0, min(100.0, comp_score))

    if comp_score >= 85.0:
        tier = "TIER_1_EXCELLENT"
    elif comp_score >= 70.0:
        tier = "TIER_2_GOOD"
    else:
        tier = "TIER_3_UNDERPERFORMING"

    return ContractorScorecard(
        contractor_id=contractor_id,
        department=department,
        total_assigned_jobs=total,
        completed_jobs=completed,
        sla_compliant_jobs=sla_compliant,
        sla_compliance_rate_pct=sla_pct,
        mean_time_to_resolution_hours=mttr,
        dispute_count=disputes,
        dispute_rate_pct=disp_pct,
        composite_performance_score=comp_score,
        performance_tier=tier,
    )
