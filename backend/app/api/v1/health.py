"""Health check endpoint.

Matches ``GET /api/v1/health`` from the Key Endpoints list in
``.helix/ARCHITECTURE.md`` — used as the Container Apps liveness probe.
"""

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return a simple liveness indicator."""

    return HealthResponse(status="ok")
