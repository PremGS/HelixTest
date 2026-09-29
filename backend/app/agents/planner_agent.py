"""Planner agent node.

Per the "LangGraph — Planner Agent decomposes query into sub-tasks" step in
the Multi-Agent Natural Language Query workflow in
``.helix/ARCHITECTURE.md``.
"""

from __future__ import annotations

from app.agents.state import QueryAgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def planner_agent(state: QueryAgentState) -> QueryAgentState:
    """Decompose the incoming query into sub-tasks.

    TODO: replace this stub with a LangChain chain (e.g. an LLM prompted to
    output a JSON list of sub-tasks) driven by
    ``OpenAIService.chat_completion``.
    """

    query = state.get("query", "")
    logger.debug("planner_agent decomposing query: %s", query)

    # Stub: treat the whole query as a single sub-task.
    sub_tasks = [query] if query else []
    return {**state, "sub_tasks": sub_tasks}
