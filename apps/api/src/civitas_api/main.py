from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from civitas_api.core.config import get_settings
from civitas_api.routers import health, reports

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
