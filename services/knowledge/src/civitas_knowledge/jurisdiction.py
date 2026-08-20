"""Statutory Jurisdictional Boundary Resolver.

Pins legal statutory maintenance responsibility (National Highway Authority, State PWD,
Municipal Corporation, Metro Transit, or Private Residential Layout) to eliminate
inter-departmental ping-pong and misrouted work orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

JurisdictionType = Literal[
    "MUNICIPAL_CORPORATION",
    "NATIONAL_HIGHWAY_AUTHORITY",
    "STATE_PUBLIC_WORKS",
    "METRO_TRANSIT_AUTHORITY",
    "PRIVATE_RESIDENTIAL_LAYOUT",
]


@dataclass(frozen=True)
class JurisdictionalAssignment:
    jurisdiction: JurisdictionType
    governing_agency: str
    statutory_act_reference: str
    statutory_sla_hours: int
    inter_agency_escalation_protocol: str
    is_municipal_responsibility: bool


def resolve_jurisdiction(
    latitude: float,
    longitude: float,
    road_classification: str | None = None,
    landmark_context: str | None = None,
) -> JurisdictionalAssignment:
    """Determines statutory maintenance jurisdiction and legal SLA boundaries."""
    road_cls = (road_classification or "").lower()
    lm = (landmark_context or "").lower()

    if "national_highway" in road_cls or "nh-" in lm or "expressway" in road_cls or "nhai" in lm:
        return JurisdictionalAssignment(
            jurisdiction="NATIONAL_HIGHWAY_AUTHORITY",
            governing_agency="National Highways Authority of India (NHAI) Project Implementation Unit",
            statutory_act_reference="National Highways Act 1956 §4 / Concessionaire Maintenance Protocol",
            statutory_sla_hours=12,
            inter_agency_escalation_protocol="Direct escalation to NHAI Regional Highway Corridor Engineer & Toll Concessionaire Patrol",
            is_municipal_responsibility=False,
        )

    if "state_highway" in road_cls or "sh-" in lm or "arterial_pwd" in road_cls or "pwd" in lm:
        return JurisdictionalAssignment(
            jurisdiction="STATE_PUBLIC_WORKS",
            governing_agency="State Public Works Department (Roads & Bridges Division)",
            statutory_act_reference="State Highways & Arterial Corridors Regulation 1964 §12",
            statutory_sla_hours=24,
            inter_agency_escalation_protocol="Transferred to PWD Executive Engineer with automated municipal tracking mirror",
            is_municipal_responsibility=False,
        )

    if "metro" in lm or "transit" in lm or "rail" in lm or "metro_corridor" in road_cls:
        return JurisdictionalAssignment(
            jurisdiction="METRO_TRANSIT_AUTHORITY",
            governing_agency="Urban Mass Rapid Transit Corporation (Civil Infrastructure Wing)",
            statutory_act_reference="Metro Railways (Operation and Maintenance) Act §33",
            statutory_sla_hours=6,
            inter_agency_escalation_protocol="Immediate alert to Metro Line Safety & Track Clearance Inspector",
            is_municipal_responsibility=False,
        )

    if "private" in road_cls or "gated_community" in lm or "society" in lm or "apartment_layout" in road_cls:
        return JurisdictionalAssignment(
            jurisdiction="PRIVATE_RESIDENTIAL_LAYOUT",
            governing_agency="Resident Welfare Association (RWA) / Private Property Management",
            statutory_act_reference="Municipal Corporation By-laws 2018 (Private Estate Internal Common Areas §9)",
            statutory_sla_hours=48,
            inter_agency_escalation_protocol="Notice served to Society Management with Municipal Environmental Health Oversight",
            is_municipal_responsibility=False,
        )

    # Standard Municipal Ward Authority
    return JurisdictionalAssignment(
        jurisdiction="MUNICIPAL_CORPORATION",
        governing_agency="Municipal Corporation Ward Maintenance & Engineering Division",
        statutory_act_reference="Municipal Corporation Act §284 (Public Streets & Stormwater Maintenance)",
        statutory_sla_hours=24,
        inter_agency_escalation_protocol="Dispatched to Ward Junior Engineer & Quick Response Repair Crew",
        is_municipal_responsibility=True,
    )
