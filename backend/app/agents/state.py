"""Shared state type for the LangGraph query pipeline."""

from __future__ import annotations

from typing import Optional, TypedDict


class QueryAgentState(TypedDict, total=False):
    """State threaded through the planner -> retrieval -> critique graph.

    Attributes:
        query: The original natural language query text.
        sub_tasks: Sub-tasks the planner agent decomposed the query into.
        retrieved_chunks: Document chunks assembled by the retrieval agent.
        context_score: Best relevance score among retrieved chunks, used to
            decide the "Sufficient context" vs "Insufficient context" branch.
        answer: The generated answer text.
        confidence_score: Critique agent's confidence in ``answer``.
        low_confidence: Whether the critique agent flagged this as a
            low-confidence / fallback response.
    """

    query: str
    sub_tasks: list[str]
    retrieved_chunks: list[dict]
    context_score: float
    answer: Optional[str]
    confidence_score: Optional[float]
    low_confidence: bool
