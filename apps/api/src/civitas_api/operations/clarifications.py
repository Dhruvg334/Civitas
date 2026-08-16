"""Clarification persistence + lifecycle.

The contract (ref/04 §7) treats clarification as a one-shot per report.
However (incident_id, question_id) is intentionally NOT unique at the DB
level — see migration 0004. The same question may legitimately be re-asked
after an incident is reopened. This module enforces "at most one *open*
clarification per (incident, question)" at the application layer.

When all *required* questions are answered, the incident advances back to
``under_analysis`` (it was put into ``awaiting_clarification`` by the ask).
"""

from __future__ import annotations

import uuid as _uuid
from datetime import UTC, datetime
from typing import Any

from civitas_api.core.database import get_connection
from civitas_api.operations import reports as reports_ops
from civitas_api.operations.state_machine import assert_incident_transition


def _now() -> datetime:
    return datetime.now(UTC)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


def ask_clarifications(
    incident_id: str,
    questions: list[dict[str, Any]],
    asked_by: str,
) -> list[dict[str, Any]]:
    """Persist a batch of questions for an incident. Advances the incident
    to ``awaiting_clarification`` if not already there. Returns the persisted
    clarification rows in input order."""
    target = reports_ops.get_incident(incident_id)
    if target is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="incident not found")

    current_status = target.get("status") or "submitted"
    if current_status in {"submitted", "under_analysis", "reopened"}:
        assert_incident_transition(current_status, "awaiting_clarification")

    now = _now()
    persisted: list[dict[str, Any]] = []

    with get_connection() as conn, conn.cursor() as cur:
        if current_status in {"submitted", "under_analysis", "reopened"}:
            cur.execute(
                "UPDATE incidents SET status = 'awaiting_clarification', "
                "status_updated_at = %(now)s WHERE incident_id = %(i)s",
                {"now": now, "i": incident_id},
            )
        for q in questions:
            qid = q.get("question_id") or _gen_id("q")
            # App-level uniqueness on open (incident, question).
            cur.execute(
                "SELECT 1 FROM clarifications "
                "WHERE incident_id = %(i)s AND question_id = %(q)s "
                "AND answered_at IS NULL",
                {"i": incident_id, "q": qid},
            )
            if cur.fetchone() is not None:
                # Skip silently — re-asking an already-open question is a
                # no-op rather than a duplicate row.
                continue
            clarification_id = _gen_id("cla")
            cur.execute(
                "INSERT INTO clarifications "
                "(clarification_id, incident_id, question_id, question_text, "
                "decision_impact, required, asked_at) "
                "VALUES (%(id)s, %(i)s, %(q)s, %(t)s, %(di)s, %(r)s, %(now)s)",
                {
                    "id": clarification_id,
                    "i": incident_id,
                    "q": qid,
                    "t": q.get("text") or "",
                    "di": reports_ops.to_json(q.get("decision_impact") or []),
                    "r": bool(q.get("required", False)),
                    "now": now,
                },
            )
            cur.execute(
                "SELECT * FROM clarifications WHERE clarification_id = %(id)s",
                {"id": clarification_id},
            )
            persisted.append(dict(cur.fetchone() or {}))
        conn.commit()

    return persisted


def answer_clarification(
    incident_id: str,
    question_id: str,
    answer_text: str,
    answered_by: str,
) -> dict[str, Any]:
    """Persist an answer to one clarification. If this completes the set of
    required questions, advance the incident back to ``under_analysis``."""
    now = _now()
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM clarifications "
            "WHERE incident_id = %(i)s AND question_id = %(q)s "
            "ORDER BY asked_at DESC LIMIT 1",
            {"i": incident_id, "q": question_id},
        )
        row = cur.fetchone()
        if row is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=404, detail="clarification not found"
            )
        existing = dict(row)
        if existing.get("answered_at") is not None:
            # Idempotent re-answer: overwrite the previous answer.
            pass
        cur.execute(
            "UPDATE clarifications "
            "SET answer_text = %(a)s, answered_at = %(now)s, answered_by = %(by)s "
            "WHERE clarification_id = %(id)s",
            {
                "a": answer_text,
                "now": now,
                "by": answered_by,
                "id": existing["clarification_id"],
            },
        )

        # Are all required Q's for this incident now answered?
        cur.execute(
            "SELECT COUNT(*) AS unanswered_required FROM clarifications "
            "WHERE incident_id = %(i)s AND required = 1 AND answered_at IS NULL",
            {"i": incident_id},
        )
        unans = int(cur.fetchone()["unanswered_required"])

        incident = reports_ops.get_incident(incident_id)
        if incident is not None and unans == 0:
            cur_status = incident.get("status") or "submitted"
            if cur_status == "awaiting_clarification":
                assert_incident_transition("awaiting_clarification", "under_analysis")
                cur.execute(
                    "UPDATE incidents SET status = 'under_analysis', "
                    "status_updated_at = %(now)s WHERE incident_id = %(i)s",
                    {"now": now, "i": incident_id},
                )
        conn.commit()
        cur.execute(
            "SELECT * FROM clarifications WHERE clarification_id = %(id)s",
            {"id": existing["clarification_id"]},
        )
        return dict(cur.fetchone() or {})


def list_clarifications(incident_id: str) -> list[dict[str, Any]]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM clarifications WHERE incident_id = %(i)s "
            "ORDER BY asked_at ASC",
            {"i": incident_id},
        )
        rows = list(cur.fetchall())
    return [dict(r) for r in rows]