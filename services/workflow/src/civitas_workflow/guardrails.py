"""Adversarial Hallucination Guardrail & Citation Verification Node.

Validates routing proposals, SLA targets, and work order equipment against
retrieved statutory policy citations and municipal catalog boundaries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

VALID_MUNICIPAL_DEPARTMENTS = {
    "water_supply",
    "water_and_sewerage",
    "road_maintenance",
    "public_works",
    "electrical_engineering",
    "streetlighting",
    "solid_waste_management",
    "parks_and_urban_forestry",
    "stormwater_drainage",
    "traffic_engineering",
    "emergency_response",
}

INJECTION_PATTERNS = [
    r"ignore (all|previous|prior) instructions",
    r"bypass (human|policy|security|triage) review",
    r"mark (as )?resolved without (inspection|repair|verification)",
    r"escalate to level 0 admin",
    r"system prompt override",
]


@dataclass(frozen=True)
class GuardrailViolation:
    field: str
    code: str
    message: str
    severity: str  # "warning" or "critical"


@dataclass(frozen=True)
class GuardrailVerificationResult:
    is_valid: bool
    requires_human_triage: bool
    violations: list[GuardrailViolation]
    sanitized_department: str
    target_sla_hours: int
    rejection_reason: str | None


def verify_routing_and_work_order_guardrails(
    proposed_department: str,
    target_sla_hours: int,
    work_order_tasks: list[str],
    retrieved_policy_citations: list[str] | None = None,
    raw_citizen_text: str | None = None,
) -> GuardrailVerificationResult:
    """Verifies that agent proposals are grounded in policy and free of hallucinated entities or prompt injection."""
    violations: list[GuardrailViolation] = []
    dept_norm = proposed_department.strip().lower().replace("-", "_").replace(" ", "_")

    # 1. Prompt Injection Check on citizen input
    if raw_citizen_text:
        for pat in INJECTION_PATTERNS:
            if re.search(pat, raw_citizen_text, re.IGNORECASE):
                violations.append(
                    GuardrailViolation(
                        field="citizen_text",
                        code="PROMPT_INJECTION_DETECTED",
                        message="Potential adversarial prompt injection pattern detected in input text.",
                        severity="critical",
                    )
                )

    # 2. Hallucinated Department Verification
    if dept_norm not in VALID_MUNICIPAL_DEPARTMENTS:
        # Check if department matches valid token
        matched_dept = None
        for valid_d in VALID_MUNICIPAL_DEPARTMENTS:
            if any(tok in valid_d for tok in dept_norm.split("_") if len(tok) > 3):
                matched_dept = valid_d
                break

        if matched_dept:
            dept_norm = matched_dept
            violations.append(
                GuardrailViolation(
                    field="department",
                    code="DEPARTMENT_NORMALIZED",
                    message=f"Department '{proposed_department}' normalized to statutory catalog entity '{matched_dept}'.",
                    severity="warning",
                )
            )
        else:
            violations.append(
                GuardrailViolation(
                    field="department",
                    code="HALLUCINATED_DEPARTMENT",
                    message=f"Department '{proposed_department}' is not a recognized municipal authority.",
                    severity="critical",
                )
            )
            dept_norm = "public_works"

    # 3. SLA Boundary Verification
    final_sla = target_sla_hours
    if target_sla_hours < 2 or target_sla_hours > 168:
        violations.append(
            GuardrailViolation(
                field="target_sla_hours",
                code="SLA_OUT_OF_BOUNDS",
                message=f"Proposed SLA of {target_sla_hours} hours is outside statutory 2h - 168h envelope.",
                severity="warning",
            )
        )
        final_sla = max(2, min(168, target_sla_hours))

    # 4. Citation Grounding Check
    citations = retrieved_policy_citations or []
    if not citations:
        violations.append(
            GuardrailViolation(
                field="citations",
                code="UNGROUNDED_PROPOSAL",
                message="Proposal lacks explicit statutory policy citation backing.",
                severity="warning",
            )
        )

    # 5. Work Order Task Validation
    if not work_order_tasks:
        violations.append(
            GuardrailViolation(
                field="work_order_tasks",
                code="EMPTY_WORK_ORDER",
                message="Work order requires at least one operational task.",
                severity="critical",
            )
        )

    has_critical = any(v.severity == "critical" for v in violations)
    is_valid = not has_critical
    rejection = "; ".join(v.message for v in violations if v.severity == "critical") if has_critical else None

    return GuardrailVerificationResult(
        is_valid=is_valid,
        requires_human_triage=has_critical or len(violations) > 1,
        violations=violations,
        sanitized_department=dept_norm,
        target_sla_hours=final_sla,
        rejection_reason=rejection,
    )
