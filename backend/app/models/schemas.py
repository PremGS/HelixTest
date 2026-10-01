"""Pydantic schemas for the SLLIP backend.

These models mirror the entities in the Cosmos DB ER diagram defined in
``.helix/ARCHITECTURE.md`` (USER, SESSION, DOCUMENT, DOCUMENT_CHUNK, QUERY,
QUERY_RESULT, CONVERSATION, CONVERSATION_MESSAGE, AUDIT_LOG,
DOCUMENT_PERMISSION), plus request/response models used by the API layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class User(BaseModel):
    """Mirrors the USER entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    role: str
    department: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class Session(BaseModel):
    """Mirrors the SESSION entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    cats_token_ref: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class Document(BaseModel):
    """Mirrors the DOCUMENT entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    blob_url: Optional[str] = None
    original_filename: str
    mime_type: str
    file_size_bytes: int
    processing_status: str = "UPLOADED"
    index_id: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DocumentChunk(BaseModel):
    """Mirrors the DOCUMENT_CHUNK entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    chunk_index: int
    content_text: str
    embedding_id: Optional[str] = None
    search_index_key: Optional[str] = None
    token_count: int
    indexed_at: Optional[datetime] = None


class Query(BaseModel):
    """Mirrors the QUERY entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    session_id: str
    natural_language_input: str
    query_status: str = "QUEUED"
    agent_pipeline_trace: Optional[str] = None
    total_tokens_used: int = 0
    submitted_at: datetime
    completed_at: Optional[datetime] = None


class QueryResult(BaseModel):
    """Mirrors the QUERY_RESULT entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    query_id: str
    generated_answer: str
    confidence_score: float
    model_version: str
    citations: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    generated_at: datetime


class Conversation(BaseModel):
    """Mirrors the CONVERSATION entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    last_message_at: Optional[datetime] = None
    is_archived: bool = False


class ConversationMessage(BaseModel):
    """Mirrors the CONVERSATION_MESSAGE entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    query_id: Optional[str] = None
    role: str
    content: str
    sequence_number: int
    created_at: datetime


class AuditLog(BaseModel):
    """Mirrors the AUDIT_LOG entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resource_type: str
    resource_id: str
    action: str
    outcome: str
    ip_address: Optional[str] = None
    details: Optional[str] = None
    timestamp: datetime


class DocumentPermission(BaseModel):
    """Mirrors the DOCUMENT_PERMISSION entity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    user_id: str
    permission_level: str
    granted_at: datetime
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# API request/response models
# ---------------------------------------------------------------------------


class DocumentUploadResponse(BaseModel):
    """Response returned by ``POST /api/v1/documents/upload``."""

    document_id: str
    status: str = "PROCESSING"


class DocumentStatusResponse(BaseModel):
    """Response returned by ``GET /api/v1/documents/{document_id}/status``."""

    document_id: str
    status: str
    chunk_count: int = 0
    indexed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class QuerySubmitRequest(BaseModel):
    """Request body for ``POST /api/v1/queries``."""

    query_text: str = Field(..., description="Natural language query text")
    session_id: str
    document_filters: Optional[list[str]] = Field(
        default=None, description="Optional list of document IDs to scope the query to"
    )


class QuerySubmitResponse(BaseModel):
    """Response returned by ``POST /api/v1/queries``."""

    query_id: str
    status: str = "QUEUED"


class QueryResultResponse(BaseModel):
    """Response returned by ``GET /api/v1/queries/{query_id}/result``."""

    query_id: str
    status: str
    generated_answer: Optional[str] = None
    confidence_score: Optional[float] = None
    citations: Optional[str] = None


class AuditTrailResponse(BaseModel):
    """Response returned by ``GET /api/v1/audit/trail``."""

    entries: list[AuditLog]
    total_count: int
    page: int
    limit: int


class ConversationHistoryResponse(BaseModel):
    """Response returned by ``GET /api/v1/conversations/{session_id}``."""

    conversation: Optional[Conversation] = None
    messages: list[ConversationMessage] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response returned by ``GET /api/v1/health``."""

    status: str = "ok"
