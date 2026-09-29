"""Query endpoints.

Implements ``POST /queries`` and ``GET /queries/{query_id}/result`` from the
Key Endpoints list, matching the Multi-Agent Natural Language Query & AI
Analysis Workflow sequence diagram in ``.helix/ARCHITECTURE.md``.
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.models.schemas import (
    QueryResultResponse,
    QuerySubmitRequest,
    QuerySubmitResponse,
    User,
)
from app.services.orchestration_service import OrchestrationService, QueryNotFoundError

router = APIRouter(prefix="/queries", tags=["queries"])

# Module-level singleton so the in-memory stub result store persists across
# requests within a single process. TODO: remove once results are persisted
# in Cosmos DB instead of in-process memory.
_orchestration_service = OrchestrationService()


def get_orchestration_service() -> OrchestrationService:
    """Dependency provider for :class:`OrchestrationService`.

    Returns the same module-level instance on every call so the in-memory
    stub result store in ``OrchestrationService`` persists across requests
    within a single process (e.g. between a ``POST /queries`` call and a
    subsequent ``GET /queries/{id}/result`` poll). TODO: remove this
    singleton once results are persisted in Cosmos DB instead of in-process
    memory.
    """

    return _orchestration_service


@router.post("", response_model=QuerySubmitResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_query(
    request: QuerySubmitRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
) -> QuerySubmitResponse:
    """Submit a natural language query to the multi-agent pipeline.

    Returns immediately with status ``QUEUED`` while the LangGraph pipeline
    (see ``app/agents/graph.py``) runs in a FastAPI background task via
    ``OrchestrationService.process_query``.

    TODO: persist a QUERY record (status ``QUEUED``) in Cosmos DB, and
    replace the ``BackgroundTasks`` scheduling below with a durable queue
    trigger / Azure Container Apps job so processing survives a service
    restart.
    """

    query_id = await orchestration_service.submit_query(
        query_text=request.query_text,
        session_id=request.session_id,
        user_id=user.id,
        document_filters=request.document_filters,
    )
    background_tasks.add_task(
        orchestration_service.process_query, query_id=query_id, query_text=request.query_text
    )
    return QuerySubmitResponse(query_id=query_id, status="QUEUED")


@router.get("/{query_id}/result", response_model=QueryResultResponse)
async def get_query_result(
    query_id: str,
    user: User = Depends(get_current_user),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
) -> QueryResultResponse:
    """Retrieve the AI-generated analysis result for a previously submitted query.

    TODO: join QUERY + QUERY_RESULT records from Cosmos DB.
    """

    try:
        return await orchestration_service.get_query_result(query_id=query_id)
    except QueryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
        ) from exc
