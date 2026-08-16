import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from civitas_api.core.config import get_settings
from civitas_api.routers import (
    auth,
    clarifications,
    health,
    incidents,
    incidents_ops,
    map_extract,
    media,
    ml_internal,
    policies,
    reports,
    resolutions,
    routing,
    work_orders,
    workflows,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Own the optional production LangGraph saver for the app lifetime."""
    checkpoint_url = os.getenv("CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL", "").strip()
    if checkpoint_url and not settings.database_url.startswith("sqlite:///"):
        from civitas_workflow.runtime import (
            create_postgres_checkpointer,
            create_production_workflow,
        )

        from civitas_api.services.workflow_runtime import WorkflowRuntimeService

        saver = create_postgres_checkpointer(checkpoint_url)
        saver.setup()
        app.state.workflow_runtime = WorkflowRuntimeService(
            create_production_workflow(
                checkpointer=saver, prompt_root=__import__("pathlib").Path("prompts")
            )
        )
        app.state.workflow_checkpointer = saver
    yield
    saver = getattr(app.state, "workflow_checkpointer", None)
    if saver is not None and hasattr(saver, "close"):
        saver.close()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
