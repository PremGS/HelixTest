"""Conversation history endpoint.

Implements ``GET /conversations/{session_id}`` from the Key Endpoints list.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.schemas import ConversationHistoryResponse, User

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{session_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    user: User = Depends(get_current_user),
) -> ConversationHistoryResponse:
    """Retrieve the full conversation history for a session.

    TODO: replace this stubbed empty response with a real call to
    ``CosmosService.get_conversation_history``, which should query
    CONVERSATION + CONVERSATION_MESSAGE by ``session_id`` ordered by
    ``sequence_number``, then join QUERY_RESULT records for each assistant
    message, per the conversation-drill-down flow in
    ``.helix/ARCHITECTURE.md``.
    """

    return ConversationHistoryResponse(conversation=None, messages=[])
