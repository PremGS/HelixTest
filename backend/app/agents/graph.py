"""Builds the LangGraph ``StateGraph`` wiring planner -> retrieval -> critique.

Mirrors the "Multi-Agent Natural Language Query & AI Analysis Workflow"
sequence diagram in ``.helix/ARCHITECTURE.md``, including the conditional
branch between the "Sufficient context retrieved (score > threshold)" and
"Insufficient context — fallback needed" paths.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.critique_agent import critique_agent
from app.agents.planner_agent import planner_agent
from app.agents.retrieval_agent import CONTEXT_SCORE_THRESHOLD, retrieval_agent
from app.agents.state import QueryAgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def _generate_answer(state: QueryAgentState) -> QueryAgentState:
    """Generate the primary answer when sufficient context was retrieved.

    TODO: call ``OpenAIService.chat_completion`` with the system prompt +
    assembled context window + query, per the "Sufficient context retrieved"
    branch of the workflow diagram.
    """

    query = state.get("query", "")
    return {**state, "answer": f"[stub answer for query: {query!r}]"}


def _generate_fallback_answer(state: QueryAgentState) -> QueryAgentState:
    """Generate a low-confidence, partial answer when context is insufficient.

    TODO: call ``OpenAIService.chat_completion`` with partial context and a
    disclaimer prompt, per the "Insufficient context — fallback needed"
    branch of the workflow diagram.
    """

    query = state.get("query", "")
    return {**state, "answer": f"[stub low-confidence answer for query: {query!r}]"}


def _has_sufficient_context(state: QueryAgentState) -> str:
    """Conditional-edge router matching the workflow diagram's ``alt`` branch."""

    if state.get("context_score", 0.0) > CONTEXT_SCORE_THRESHOLD:
        return "sufficient_context"
    return "insufficient_context"


def build_query_graph() -> CompiledStateGraph:
    """Build and compile the planner -> retrieval -> critique ``StateGraph``.

    Returns a compiled LangGraph runnable exposing ``.invoke(state)``.
    """

    graph = StateGraph(QueryAgentState)

    graph.add_node("planner", planner_agent)
    graph.add_node("retrieval", retrieval_agent)
    graph.add_node("generate_answer", _generate_answer)
    graph.add_node("generate_fallback_answer", _generate_fallback_answer)
    graph.add_node("critique", critique_agent)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retrieval")

    graph.add_conditional_edges(
        "retrieval",
        _has_sufficient_context,
        {
            "sufficient_context": "generate_answer",
            "insufficient_context": "generate_fallback_answer",
        },
    )

    graph.add_edge("generate_answer", "critique")
    graph.add_edge("generate_fallback_answer", "critique")
    graph.add_edge("critique", END)

    logger.debug("Compiled query LangGraph StateGraph")
    return graph.compile()
