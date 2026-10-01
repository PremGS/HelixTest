"""Stub wrapper around the Azure Cosmos DB client.

See the "Azure Cosmos DB" component and Database Design section in
``.helix/ARCHITECTURE.md``: the primary operational store for agent state,
audit trails, and vector metadata, with containers for users, sessions,
documents, document_chunks, queries, query_results, conversations,
conversation_messages, audit_log, and document_permissions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.config import get_settings
from app.models.schemas import (
    AuditLog,
    Conversation,
    ConversationHistoryResponse,
    ConversationMessage,
    Document,
    DocumentChunk,
    DocumentPermission,
    Query,
    QueryResult,
    Session,
    User,
)

CONTAINERS = (
    "users",
    "sessions",
    "documents",
    "document_chunks",
    "queries",
    "query_results",
    "conversations",
    "conversation_messages",
    "audit_log",
    "document_permissions",
)


class CosmosService:
    """Thin async wrapper around ``azure.cosmos.aio.CosmosClient``.

    Exposes narrow, container-specific CRUD helpers rather than a generic
    query API, so callers don't need to know Cosmos DB SDK details.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        # TODO: instantiate azure.cosmos.aio.CosmosClient using Managed
        # Identity (or the account key for local dev only) and cache
        # container clients for each entry in ``CONTAINERS``.
        self._client = None

    # -- users -----------------------------------------------------------
    async def get_user(self, user_id: str) -> Optional[User]:
        raise NotImplementedError("CosmosService.get_user is not implemented")

    async def upsert_user(self, user: User) -> User:
        raise NotImplementedError("CosmosService.upsert_user is not implemented")

    # -- sessions ----------------------------------------------------------
    async def get_session(self, session_id: str) -> Optional[Session]:
        raise NotImplementedError("CosmosService.get_session is not implemented")

    # -- documents ---------------------------------------------------------
    async def create_document(self, document: Document) -> Document:
        raise NotImplementedError("CosmosService.create_document is not implemented")

    async def get_document(self, document_id: str) -> Optional[Document]:
        raise NotImplementedError("CosmosService.get_document is not implemented")

    async def update_document_status(self, document_id: str, status: str) -> None:
        raise NotImplementedError(
            "CosmosService.update_document_status is not implemented"
        )

    async def delete_document(self, document_id: str) -> None:
        raise NotImplementedError("CosmosService.delete_document is not implemented")

    # -- document_chunks -----------------------------------------------------
    async def create_document_chunks(self, chunks: list[DocumentChunk]) -> None:
        raise NotImplementedError(
            "CosmosService.create_document_chunks is not implemented"
        )

    # -- queries -------------------------------------------------------------
    async def create_query(self, query: Query) -> Query:
        raise NotImplementedError("CosmosService.create_query is not implemented")

    async def get_query(self, query_id: str) -> Optional[Query]:
        raise NotImplementedError("CosmosService.get_query is not implemented")

    async def update_query_status(self, query_id: str, status: str) -> None:
        raise NotImplementedError(
            "CosmosService.update_query_status is not implemented"
        )

    # -- query_results ---------------------------------------------------------
    async def create_query_result(self, result: QueryResult) -> QueryResult:
        raise NotImplementedError(
            "CosmosService.create_query_result is not implemented"
        )

    async def get_query_result(self, query_id: str) -> Optional[QueryResult]:
        raise NotImplementedError("CosmosService.get_query_result is not implemented")

    # -- conversations / conversation_messages --------------------------------
    async def get_conversation_history(
        self, session_id: str
    ) -> ConversationHistoryResponse:
        """Return the conversation + ordered messages for ``session_id``.

        TODO: query CONVERSATION by session_id, then CONVERSATION_MESSAGE
        ordered by sequence_number, joining QUERY_RESULT for assistant
        messages.
        """

        raise NotImplementedError(
            "CosmosService.get_conversation_history is not implemented"
        )

    async def append_conversation_message(
        self, message: ConversationMessage
    ) -> ConversationMessage:
        raise NotImplementedError(
            "CosmosService.append_conversation_message is not implemented"
        )

    # -- audit_log -------------------------------------------------------------
    async def insert_audit_log(self, entry: AuditLog) -> AuditLog:
        raise NotImplementedError("CosmosService.insert_audit_log is not implemented")

    async def query_audit_log(
        self,
        from_: Optional[datetime] = None,
        to: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Return a page of audit log entries ordered by timestamp desc.

        TODO: query the ``audit_log`` container filtered by the given date
        range with pagination.
        """

        raise NotImplementedError("CosmosService.query_audit_log is not implemented")

    # -- document_permissions ---------------------------------------------------
    async def list_document_permissions(
        self, document_id: str
    ) -> list[DocumentPermission]:
        raise NotImplementedError(
            "CosmosService.list_document_permissions is not implemented"
        )
