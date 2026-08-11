"""Policy / playbook persistence + retrieval.

Two read endpoints:

    GET /api/v1/policies?category=&department=&kind=
    GET /api/v1/policies/{code}

Filter combinations:
- ``kind=playbook`` + ``category=water_leakage`` -> WATER playbooks
- ``kind=policy`` + ``department=water_supply`` -> WATER policies

Empty filters return everything (TRIAGE role).
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from typing import Any

from civitas_api.core.database import get_connection


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{_uuid.uuid4().hex}"


def _row_to_dict(row: Any) -> dict[str, Any]:
    d = dict(row)
    for key in ("categories", "departments", "required_actions", "suggested_resources",
                "severity_factors", "priority_factors"):
        v = d.get(key)
        if isinstance(v, str):
            import json as _json
            try:
                d[key] = _json.loads(v)
            except (ValueError, TypeError):
                pass
    return d


def list_policies(
    category: str | None = None,
    department: str | None = None,
    kind: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    sql = "SELECT * FROM policies WHERE 1=1"
    params: dict[str, Any] = {"limit": limit}

    # The GIN indexes let us use @> containment. For sqlite we fall back to
    # LIKE on the serialized JSON.
    from civitas_api.core.config import get_settings
    is_sqlite = get_settings().database_url.startswith("sqlite:///")

    if category:
        if is_sqlite:
            sql += " AND categories LIKE %(cat)s"
            params["cat"] = f'%"{category}"%'
        else:
            sql += " AND categories @> %(cat)s"
            params["cat"] = [category]
    if department:
        if is_sqlite:
            sql += " AND departments LIKE %(dept)s"
            params["dept"] = f'%"{department}"%'
        else:
            sql += " AND departments @> %(dept)s"
            params["dept"] = [department]
    if kind:
        sql += " AND kind = %(kind)s"
        params["kind"] = kind
    sql += " ORDER BY code ASC LIMIT %(limit)s"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = list(cur.fetchall())
    return [_row_to_dict(r) for r in rows]


def get_policy_by_code(code: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM policies WHERE code = %(c)s", {"c": code})
            row = cur.fetchone()
    return _row_to_dict(row) if row else None


def get_policy(policy_id: str) -> dict[str, Any] | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM policies WHERE policy_id = %(id)s", {"id": policy_id})
            row = cur.fetchone()
    return _row_to_dict(row) if row else None


def upsert_policy(
    code: str,
    kind: str,
    title: str,
    body: str,
    categories: list[str],
    departments: list[str],
    severity_factors: list[dict[str, Any]],
    priority_factors: list[dict[str, Any]],
    required_actions: list[str],
    suggested_resources: list[str],
) -> dict[str, Any]:
    """Used by the seed migration (and admin tooling). Idempotent on code."""
    from civitas_api.operations import reports as reports_ops

    now = _now()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT policy_id FROM policies WHERE code = %(c)s",
                {"c": code},
            )
            row = cur.fetchone()
            if row is not None:
                pid = row["policy_id"]
                cur.execute(
                    "UPDATE policies SET kind = %(k)s, title = %(t)s, body = %(b)s, "
                    "categories = %(cat)s, departments = %(dept)s, "
                    "severity_factors = %(sf)s, priority_factors = %(pf)s, "
                    "required_actions = %(ra)s, suggested_resources = %(sr)s "
                    "WHERE policy_id = %(id)s",
                    {
                        "k": kind, "t": title, "b": body,
                        "cat": reports_ops.to_json(categories),
                        "dept": reports_ops.to_json(departments),
                        "sf": reports_ops.to_json(severity_factors),
                        "pf": reports_ops.to_json(priority_factors),
                        "ra": reports_ops.to_json(required_actions),
                        "sr": reports_ops.to_json(suggested_resources),
                        "id": pid,
                    },
                )
            else:
                pid = _gen_id("pol")
                cur.execute(
                    "INSERT INTO policies "
                    "(policy_id, code, kind, title, body, categories, departments, "
                    "severity_factors, priority_factors, required_actions, "
                    "suggested_resources, created_at) "
                    "VALUES (%(id)s, %(c)s, %(k)s, %(t)s, %(b)s, %(cat)s, %(dept)s, "
                    "%(sf)s, %(pf)s, %(ra)s, %(sr)s, %(now)s)",
                    {
                        "id": pid, "c": code, "k": kind, "t": title, "b": body,
                        "cat": reports_ops.to_json(categories),
                        "dept": reports_ops.to_json(departments),
                        "sf": reports_ops.to_json(severity_factors),
                        "pf": reports_ops.to_json(priority_factors),
                        "ra": reports_ops.to_json(required_actions),
                        "sr": reports_ops.to_json(suggested_resources),
                        "now": now,
                    },
                )
            conn.commit()
    return get_policy(pid) or {}