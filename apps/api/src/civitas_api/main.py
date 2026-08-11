from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from civitas_api.core.config import get_settings
from civitas_api.routers import (
    clarifications,
    health,
    incidents,
    incidents_ops,
    media,
    policies,
    reports,
    resolutions,
    routing,
    work_orders,
)

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(incidents_ops.router)
app.include_router(media.router)
app.include_router(work_orders.router)
app.include_router(clarifications.router)
app.include_router(routing.router)
app.include_router(resolutions.router)
app.include_router(policies.router)


@app.get("/ready")
def ready() -> dict[str, str]:
    """Liveness + DB readiness probe.

    Returns 200 even if DB is unreachable so the route can be smoke-tested
    offline; in deployment a richer check would gate on a real DB ping.
    """
    return {"service": settings.app_name, "status": "ready"}