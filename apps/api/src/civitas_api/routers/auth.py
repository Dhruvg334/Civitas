"""Authentication and user profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from civitas_api.core.auth import Principal, get_current_principal
from civitas_api.core.envelope import success_envelope

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get("/me")
def get_me(
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> dict:
    """Return the verified identity and authorization role for the caller."""
    display_name = principal.email.split("@")[0] if principal.email else principal.user_id
    return success_envelope({
        "user_id": principal.user_id,
        "email": principal.email or "",
        "role": principal.role.value,
        "display_name": display_name,
    })
