import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from civitas_api.core.config import get_settings
from civitas_api.core.envelope import error_envelope
from civitas_api.core.logging_security import install_security_logging
from civitas_api.core.rate_limit import RateLimitMiddleware
from civitas_api.routers import (
    auth,
    certificates,
    clarifications,
    clarification_channels,
    disputes,
    health,
    incidents,
    incidents_ops,
    intake_channels,
    map_extract,
    media,
    ml_internal,
    open311,
    policies,
    reports,
    resolutions,
    routing,
    telemetry,
    work_orders,
    work_orders_batch,
    workflows,
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Own the optional production LangGraph saver and logging filters."""
    install_security_logging()
    checkpoint_url = settings.workflow_checkpoint_database_url.strip()
    if checkpoint_url and not settings.database_url.startswith("sqlite:///"):
        from civitas_workflow.runtime import create_postgres_checkpointer

        from civitas_api.services.workflow_composition import create_production_runtime

        saver = create_postgres_checkpointer(checkpoint_url)
        if hasattr(saver, "setup"):
            saver.setup()  # type: ignore[attr-defined]
        app.state.workflow_runtime = create_production_runtime(saver)
        app.state.workflow_checkpointer = saver
    yield
    stored_saver = getattr(app.state, "workflow_checkpointer", None)
    if stored_saver is not None:
        connection = getattr(stored_saver, "conn", None)
        if connection is not None and hasattr(connection, "close"):
            connection.close()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

# 1. Rate limiting middleware (DDoS & DoS resource exhaustion defense)
app.add_middleware(RateLimitMiddleware)

# 2. CORS middleware (strictly validated against explicit origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Response:
    """Attach defensive HTTP security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Mask internal tracebacks and database errors in production."""
    if isinstance(exc, HTTPException):
        # Let standard HTTPExceptions pass through to their status handlers
        detail = exc.detail if isinstance(exc.detail, dict) else {
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "retryable": False,
        }
        return JSONResponse(status_code=exc.status_code, content=detail, headers=exc.headers)

    logger.exception("Unhandled application error processing request %s %s: %s", request.method, request.url.path, exc)

    if get_settings().is_production:
        return JSONResponse(
            status_code=500,
            content=error_envelope(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please contact support.",
                retryable=True,
            ),
        )

    return JSONResponse(
        status_code=500,
        content=error_envelope(
            code="INTERNAL_SERVER_ERROR",
            message=f"Unhandled error: {exc}",
            retryable=False,
        ),
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(incidents_ops.router)
app.include_router(media.router)
app.include_router(ml_internal.router)
app.include_router(work_orders.router)
app.include_router(clarifications.router)
app.include_router(routing.router)
app.include_router(resolutions.router)
app.include_router(policies.router)
app.include_router(map_extract.router)
app.include_router(workflows.router)
app.include_router(intake_channels.router)
app.include_router(open311.router)
app.include_router(telemetry.router)
app.include_router(clarification_channels.router)
app.include_router(work_orders_batch.router)
app.include_router(disputes.router)
app.include_router(certificates.router)
