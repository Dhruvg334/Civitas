"""Authentication and authorization for Civitas.

Production accepts Supabase-issued bearer tokens through either:
- legacy HS256 verification when ``SUPABASE_JWT_SECRET`` is configured; or
- Supabase's JWKS endpoint for asymmetric signing keys (RS256/ES256).

Local development keeps the existing unsigned-token convenience only when no
Supabase verifier is configured and ``CIVITAS_ENV`` is not production.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Any

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
    user_id: str
    role: Role
    email: str | None = None

    def can(self, required: Role) -> bool:
        return ROLE_RANK[self.role] >= ROLE_RANK[required]


def _normalize_role(raw: str | None) -> Role:
    if not raw:
        return Role.CITIZEN
    try:
        return Role(raw.lower())
    except ValueError:
        return Role.CITIZEN


def _pyjwt() -> Any:
    try:
        import jwt as pyjwt  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyJWT is required for authentication",
        ) from exc
    return pyjwt


def _decode_jwt(token: str) -> dict[str, Any]:
    from civitas_api.core.config import get_settings

    settings = get_settings()
    pyjwt = _pyjwt()
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None

    try:
        if settings.supabase_jwt_secret.strip():
            payload = pyjwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                options={"require": ["exp", "sub"]},
            )
            if issuer and payload.get("iss") and payload["iss"] != issuer:
                raise pyjwt.InvalidIssuerError("Invalid issuer")
            return payload

        header = pyjwt.get_unverified_header(token)
        algorithm = str(header.get("alg") or "")

        if settings.supabase_url.strip() and (settings.is_production or algorithm in {"RS256", "ES256"}):
            jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = pyjwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token)
            if algorithm not in {"RS256", "ES256"}:
                raise pyjwt.InvalidAlgorithmError(
                    f"unsupported Supabase JWT algorithm: {algorithm}"
                )
            payload = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=[algorithm],
                audience="authenticated",
                options={"require": ["exp", "sub"]},
            )
            if issuer and payload.get("iss") and payload["iss"] != issuer:
                raise pyjwt.InvalidIssuerError("Invalid issuer")
            return payload

        if settings.is_production:
            raise pyjwt.InvalidTokenError("no production JWT verifier is configured")

        # Explicit local-development fallback only.
        return pyjwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
            },
            algorithms=["HS256", "RS256", "ES256"],
        )
    except HTTPException:
        raise
    except Exception as exc:  # PyJWT raises several InvalidTokenError subclasses.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_principal(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or malformed Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = _decode_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token has no subject")

    role = _normalize_role(
        (payload.get("app_metadata") or {}).get("role") or payload.get("role")
    )
    email = payload.get("email")
    return Principal(user_id=str(sub), role=role, email=str(email) if email else None)


def require_role(minimum: Role):
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
