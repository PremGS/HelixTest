"""FastAPI Orchestration Service.

See the "FastAPI Orchestration Service" component in
``.helix/ARCHITECTURE.md``: the core backend service hosting the LangChain +
LangGraph multi-agent orchestration logic, routing queries to Azure OpenAI,
coordinating retrieval from Azure AI Search, and persisting state to Cosmos
DB.

This module provides a runnable stub: it generates deterministic mock query
ids/results so the API layer can be exercised end-to-end locally, delegating
the actual multi-agent reasoning to the LangGraph pipeline built in
``app/agents/graph.py``.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.agents.graph import build_query_graph
from app.core.logging import get_logger
from app.models.schemas import QueryResultResponse
from app.services.cosmos_service import CosmosService
from app.services.openai_service import OpenAIService
from app.services.search_service import SearchService

logger = get_logger(__name__)


class QueryNotFoundError(Exception):
    """Raised when a query_id was never submitted via :meth:`submit_query`."""


class OrchestrationService:
    """Coordinates the LangGraph multi-agent query pipeline."""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        cosmos_service: Optional[CosmosService] = None,
        openai_service: Optional[OpenAIService] = None,
    ) -> None:
        self.search_service = search_service or SearchService()
        self.cosmos_service = cosmos_service or CosmosService()
        self.openai_service = openai_service or OpenAIService()
        self._graph = build_query_graph()
        # In-memory stand-in for the Cosmos DB `queries`/`query_results`
        # containers, so this scaffold can be exercised end-to-end without a
        # real database. NOT safe for multi-worker/multi-process
        # deployments (each worker would have its own dict), and has no
        # locking around concurrent writes from background tasks — fine for
        # this single-process local scaffold, but must be replaced with real
        # Cosmos DB persistence (which handles concurrency itself, including
        # across process restarts and workers) before any production use.
        # ``_queries`` tracks ids that have been submitted (so unknown ids
        # can be distinguished from ones still processing); ``_results``
        # holds the completed pipeline output once ``process_query`` runs.
        self._queries: set[str] = set()
        self._results: dict[str, dict] = {}

    async def submit_query(
        self,
        query_text: str,
        session_id: str,
        user_id: str,
        document_filters: Optional[list[str]] = None,
    ) -> str:
        """Accept a natural language query and return immediately with a QUEUED status.

        The actual agent pipeline run is *not* awaited here — callers (the
        API layer) are expected to schedule :meth:`process_query` as a
        background task so this returns promptly, matching the 202
        Accepted / QUEUED semantics described in
        ``.helix/ARCHITECTURE.md``.

        TODO: insert a QUERY record in Cosmos DB with status ``QUEUED``
        instead of the in-memory ``self._results`` stand-in used here.
        """

        query_id = str(uuid.uuid4())
        self._queries.add(query_id)
        logger.info(
            "Stub query accepted user=%s session=%s query_id=%s", user_id, session_id, query_id
        )
        return query_id

    async def process_query(self, query_id: str, query_text: str) -> None:
        """Run the LangGraph pipeline for ``query_id`` and store its result.

        Intended to be scheduled as a background task by the API layer
        immediately after :meth:`submit_query` returns, so the pipeline runs
        without blocking the initial request/response cycle.
        """

        self._results[query_id] = await self.run_query(query_id=query_id, query_text=query_text)

    async def run_query(self, query_id: str, query_text: str) -> dict:
        """Invoke the LangGraph planner -> retrieval -> critique pipeline.

        TODO: embed ``query_text`` via ``openai_service.create_embedding``,
        run ``self._graph.ainvoke(...)`` with the initial agent state, persist
        the resulting QUERY_RESULT to Cosmos DB, and update QUERY status to
        ``COMPLETED`` or ``COMPLETED_WITH_WARNINGS`` depending on whether the
        critique agent flagged low confidence (see the "Insufficient
        context" branch in the query workflow diagram).
        """

        # Use the async entrypoint so this coroutine doesn't block the event
        # loop; LangGraph runs the (currently synchronous) node functions in
        # a worker thread under the hood.
        return await self._graph.ainvoke({"query": query_text})

    async def get_query_result(self, query_id: str) -> QueryResultResponse:
        """Retrieve the persisted result for a previously submitted query.

        Raises:
            QueryNotFoundError: if ``query_id`` was never submitted via
                :meth:`submit_query`, so callers can distinguish "unknown
                query id" (404) from "still processing" (200, status
                QUEUED).

        TODO: join QUERY + QUERY_RESULT records from Cosmos DB via
        ``cosmos_service.get_query`` / ``cosmos_service.get_query_result``,
        instead of the in-memory ``self._queries``/``self._results``
        stand-ins used here.
        """

        if query_id not in self._queries:
            raise QueryNotFoundError(query_id)

        result = self._results.get(query_id)
        if result is None:
            return QueryResultResponse(
                query_id=query_id,
                status="QUEUED",
                generated_answer=None,
                confidence_score=None,
                citations=None,
            )

        status = "COMPLETED_WITH_WARNINGS" if result.get("low_confidence") else "COMPLETED"
        return QueryResultResponse(
            query_id=query_id,
            status=status,
            generated_answer=result.get("answer"),
            confidence_score=result.get("confidence_score"),
            citations=None,
        )
