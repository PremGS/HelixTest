"""Retrieval agent node.

Per the "LangGraph — Retrieval Agent assembles context window" step in the
Multi-Agent Natural Language Query workflow in ``.helix/ARCHITECTURE.md``.
Runs a hybrid vector + keyword search against Azure AI Search for each
sub-task and assembles the resulting chunks into a context window.
"""

from __future__ import annotations

from app.agents.state import QueryAgentState
from app.core.logging import get_logger

logger = get_logger(__name__)

# Relevance score threshold used for the "Sufficient context retrieved"
# vs. "Insufficient context" branch in the query workflow diagram.
CONTEXT_SCORE_THRESHOLD = 0.5


def retrieval_agent(state: QueryAgentState) -> QueryAgentState:
    """Retrieve and assemble context for the query's sub-tasks.

    TODO: for each sub-task, generate an embedding via
    ``OpenAIService.create_embedding`` and call
    ``SearchService.hybrid_search`` to fetch the top-K relevant document
    chunks, then assemble them into a single context window for the LLM
    prompt.
    """

    sub_tasks = state.get("sub_tasks", [])
    logger.debug("retrieval_agent retrieving context for sub_tasks: %s", sub_tasks)

    # Stub: no search index wired up yet, so no chunks are retrieved and the
    # context score is left at 0.0, which will route to the "insufficient
    # context" fallback branch below.
    retrieved_chunks: list[dict] = []
    context_score = 0.0

    return {
        **state,
        "retrieved_chunks": retrieved_chunks,
        "context_score": context_score,
    }
