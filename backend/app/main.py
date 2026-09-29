"""FastAPI application entrypoint for the SLLIP backend.

Mounts the versioned API routers and exposes the health check used by the
Azure Container Apps liveness probe.
"""

from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.core.logging import configure_logging

configure_logging()

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="SLLIP backend scaffold — FastAPI Orchestration + Document Ingestion services.",
    version="0.1.0",
)

app.include_router(api_v1_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint pointing to the interactive API docs."""

    return {"message": f"{settings.app_name} is running. See /docs for API documentation."}
