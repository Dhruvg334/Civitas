"""Contractor Performance & SLA Analytics Router."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from civitas_api.core.envelope import envelope
from civitas_api.operations.reports import list_incidents
from civitas_evaluation.contractor_analytics import compute_contractor_scorecard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Contractor & SLA Analytics"])


@router.get("/contractors")
async def get_contractor_scorecards():
    """Returns SLA compliance and performance scorecards for municipal contractors."""
    incidents = list_incidents(limit=100)

    # Aggregate by assigned department
    by_dept: dict[str, list[dict]] = {}
    for inc in incidents:
        dept = inc.get("assigned_department", "water_supply")
        if dept not in by_dept:
            by_dept[dept] = []
        by_dept[dept].append({
            "status": inc.get("status", "open"),
            "duration_hours": 14.0,  # Simulated duration
            "sla_target_hours": 24.0,
            "is_disputed": inc.get("status") == "reopened_disputed",
        })

    contractor_map = {
        "water_supply": ("CONT-WAT-01", "Apex Municipal Dewatering & Pipeline Services"),
        "road_maintenance": ("CONT-RDS-02", "National Pavement & Asphalt Infrastructure Ltd"),
        "electrical_engineering": ("CONT-ELE-03", "Citywide Grid Linesmen & Luminaire Services"),
        "public_works": ("CONT-GEN-04", "Civitas Rapid Civil Response Corp"),
    }

    scorecards = []
    for dept, records in by_dept.items():
        cid, name = contractor_map.get(dept, ("CONT-GEN-00", f"{dept.title()} Maintenance Corp"))
        sc = compute_contractor_scorecard(contractor_id=cid, department=dept, job_records=records)
        scorecards.append({
            "contractor_id": sc.contractor_id,
            "contractor_name": name,
            "department": sc.department,
            "total_assigned_jobs": sc.total_assigned_jobs,
            "completed_jobs": sc.completed_jobs,
            "sla_compliant_jobs": sc.sla_compliant_jobs,
            "sla_compliance_rate_pct": sc.sla_compliance_rate_pct,
            "mean_time_to_resolution_hours": sc.mean_time_to_resolution_hours,
            "dispute_count": sc.dispute_count,
            "dispute_rate_pct": sc.dispute_rate_pct,
            "composite_performance_score": sc.composite_performance_score,
            "performance_tier": sc.performance_tier,
        })

    # Sort descending by performance score
    scorecards.sort(key=lambda x: x["composite_performance_score"], reverse=True)

    return envelope({
        "total_contractors": len(scorecards),
        "scorecards": scorecards,
    })
