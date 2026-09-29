"""Document ingestion endpoints.

Implements the ``POST /documents/upload``, ``GET
/documents/{document_id}/status``, and ``DELETE /documents/{document_id}``
endpoints from the Key Endpoints list, matching the Document Upload,
Ingestion & AI Indexing Pipeline sequence diagram in
``.helix/ARCHITECTURE.md``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, status

from app.dependencies import get_current_user
from app.models.schemas import (
    DocumentStatusResponse,
    DocumentUploadResponse,
    User,
)
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["documents"])

# Module-level singleton, consistent with the pattern used for
# ``OrchestrationService`` in ``queries.py`` — avoids constructing a new
# service (and its underlying Azure SDK clients, once implemented) per
# request.
_ingestion_service = IngestionService()


def get_ingestion_service() -> IngestionService:
    """Dependency provider for :class:`IngestionService`."""

    return _ingestion_service


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentUploadResponse:
    """Accept an uploaded document and kick off the ingestion pipeline.

    TODO: stream ``file`` to Azure Blob Storage, persist a DOCUMENT record in
    Cosmos DB with status ``UPLOADED``, and schedule the async
    extraction/chunking/embedding/indexing pipeline described in
    ``IngestionService``.
    """

    document_id = await ingestion_service.upload_document(file=file, user_id=user.id)
    return DocumentUploadResponse(document_id=document_id, status="PROCESSING")


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> DocumentStatusResponse:
    """Poll the processing status of a previously uploaded document.

    TODO: query the DOCUMENT record (and DOCUMENT_CHUNK count) from Cosmos DB.
    """

    return await ingestion_service.get_document_status(document_id=document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> None:
    """Remove a document and its associated search index entries.

    TODO: delete the blob, DOCUMENT/DOCUMENT_CHUNK records in Cosmos DB, and
    the corresponding entries in Azure AI Search.
    """

    await ingestion_service.delete_document(document_id=document_id)
