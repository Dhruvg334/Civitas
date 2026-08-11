"""Authentication and roles.

Verifies a Supabase-issued JWT (HS256) and resolves the user's role from
the `app_metadata.role` or `role` claim. Five roles are recognized:

    citizen   can submit reports, view own incidents, upload media
    triage    can list/inspect incidents, run assess
    supervisor can do everything triage can, plus merge + route
    reviewer  can approve/reject work orders, close/reopen incidents
    admin     unrestricted

Role gating is enforced via FastAPI dependencies. In tests, the
`get_current_principal` dependency is monkeypatched to return a
`Principal` directly so the same route code runs without a real JWT.

When `SUPABASE_JWT_SECRET` is empty, the dependency enters *dev mode*:
it accepts any token and decodes it without signature verification,
attaching whatever role is in the payload. This keeps local development
unblocked without weakening production (where the secret is required).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


class Role(StrEnum):
    CITIZEN = "citizen"
    TRIAGE = "triage"
    SUPERVISOR = "supervisor"
    REVIEWER = "reviewer"
    ADMIN = "admin"


ROLE_RANK: dict[Role, int] = {
    Role.CITIZEN: 1,
    Role.TRIAGE: 2,
    Role.SUPERVISOR: 3,
    Role.REVIEWER: 4,
    Role.ADMIN: 5,
}


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. Attached to every request via dependency."""

    user_id: str
    role: Role

    def can(self, required: Role) -> bool:
        return ROLE_RANK[self.role] >= ROLE_RANK[required]


def _normalize_role(raw: str | None) -> Role:
    """Map a claim value to a Role, defaulting to CITIZEN for unknown values.

    Production code should not pass unknown roles; this is lenient on
    purpose so a token issued before a role was added does not 500.
    """
    if not raw:
        return Role.CITIZEN
    try:
        return Role(raw.lower())
    except ValueError:
        return Role.CITIZEN


def _decode_jwt(token: str, secret: str | None) -> dict:
    """Decode a JWT. In dev mode (no secret), signature is not verified.

    Production must set SUPABASE_JWT_SECRET. PyJWT is a runtime dep —
    imported lazily so the package is importable in environments that
    only run schema/maintenance code.
    """
    try:
        import jwt as pyjwt  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyJWT not installed; required for auth",
        ) from exc

    if not secret:
        # Dev mode — decode without verification. Caller must override in prod.
        return pyjwt.decode(token, options={"verify_signature": False})
    return pyjwt.decode(token, secret, algorithms=["HS256"])


def get_current_principal(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Principal:
    """FastAPI dependency: extract and verify the bearer token."""
    from civitas_api.core.config import get_settings

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()
    payload = _decode_jwt(token, settings.supabase_jwt_secret or None)

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token has no subject",
        )
    role = _normalize_role(
        (payload.get("app_metadata") or {}).get("role") or payload.get("role")
    )
    return Principal(user_id=str(sub), role=role)


def require_role(minimum: Role):
    """Dependency factory: require caller to have at least `minimum` role."""

    def _check(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if not principal.can(minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role {principal.role.value} insufficient; need {minimum.value}",
            )
        return principal

    return _check
