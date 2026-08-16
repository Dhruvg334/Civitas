from fastapi import APIRouter, HTTPException, status

from civitas_api.core.config import get_settings
from civitas_api.core.database import get_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"service": "civitas-api", "status": "ok"}


@router.get("/live")
def live() -> dict[str, str]:
    return {"service": "civitas-api", "status": "alive"}


@router.get("/ready")
def ready() -> dict[str, object]:
    settings=get_settings()
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"service": "civitas-api", "status": "not_ready", "database": "unavailable", "reason": str(exc)},
        ) from exc
    return {"service": "civitas-api", "status": "ready", "database": "ok", "environment": settings.environment}
