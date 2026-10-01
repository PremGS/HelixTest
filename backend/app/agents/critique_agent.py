"""Critique agent node.

Per the "LangGraph — Critique Agent validates answer quality" step in the
Multi-Agent Natural Language Query workflow in ``.helix/ARCHITECTURE.md``.
"""

from __future__ import annotations

from app.agents.state import QueryAgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def critique_agent(state: QueryAgentState) -> QueryAgentState:
    """Validate the generated answer's quality/confidence.

    TODO: replace this stub with an LLM-based critique step (e.g. asking
    GPT-4.1 to rate the answer against the retrieved context and flag
    hallucination risk), persisting the confidence score alongside the
    QUERY_RESULT record.
    """

    low_confidence = state.get("context_score", 0.0) < 0.5
    confidence_score = 0.4 if low_confidence else 0.9

    logger.debug(
        "critique_agent confidence_score=%s low_confidence=%s",
        confidence_score,
        low_confidence,
    )

    return {
        **state,
        "confidence_score": confidence_score,
        "low_confidence": low_confidence,
    }
