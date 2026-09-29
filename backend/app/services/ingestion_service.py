"""Document Ingestion Service.

See the "Document Ingestion Service" component in
``.helix/ARCHITECTURE.md``: a dedicated microservice handling the document
upload pipeline — receive files, store raw documents in Blob Storage, trigger
Azure Document Intelligence for extraction, generate embeddings via Text
Embedding 3 Large, and index into Azure AI Search.

This module provides a runnable stub of that pipeline: it returns
deterministic mock responses so the API layer can be exercised end-to-end
locally, with ``TODO`` comments marking where each real Azure service call
belongs.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import UploadFile

from app.core.logging import get_logger
from app.models.schemas import DocumentStatusResponse
from app.services.cosmos_service import CosmosService
from app.services.openai_service import OpenAIService
from app.services.search_service import SearchService
from app.services.storage_service import StorageService

logger = get_logger(__name__)

_CHUNK_TOKEN_SIZE = 512


class IngestionService:
    """Orchestrates the document upload -> extraction -> chunk -> index pipeline."""

    def __init__(
        self,
        storage_service: Optional[StorageService] = None,
        search_service: Optional[SearchService] = None,
        cosmos_service: Optional[CosmosService] = None,
        openai_service: Optional[OpenAIService] = None,
    ) -> None:
        self.storage_service = storage_service or StorageService()
        self.search_service = search_service or SearchService()
        self.cosmos_service = cosmos_service or CosmosService()
        self.openai_service = openai_service or OpenAIService()

    async def upload_document(self, file: UploadFile, user_id: str) -> str:
        """Accept an uploaded file and start the async ingestion pipeline.

        TODO:
        1. Stream ``file`` to Blob Storage via ``storage_service.upload_blob``.
        2. Insert a DOCUMENT record in Cosmos DB with status ``UPLOADED``.
        3. Schedule ``process_document`` as a background task (e.g. via
           Azure Container Apps jobs, a queue trigger, or FastAPI
           ``BackgroundTasks``) to run steps in ``process_document`` below.
        """

        document_id = str(uuid.uuid4())
        logger.info("Stub upload accepted for user=%s document_id=%s", user_id, document_id)
        return document_id

    async def process_document(self, document_id: str) -> None:
        """Run the extraction -> chunking -> embedding -> indexing pipeline.

        TODO:
        1. Submit the blob URI to Azure Document Intelligence for layout +
           text extraction.
        2. Chunk extracted text into ~``_CHUNK_TOKEN_SIZE`` token segments
           with overlap.
        3. Generate embeddings per chunk via
           ``openai_service.create_embedding``.
        4. Batch-index chunks into Azure AI Search via
           ``search_service.index_chunks``.
        5. Persist DOCUMENT_CHUNK records and update DOCUMENT status to
           ``INDEXED`` in Cosmos DB.
        """

        raise NotImplementedError("IngestionService.process_document is not implemented")

    async def get_document_status(self, document_id: str) -> DocumentStatusResponse:
        """Return the current processing status for a document.

        TODO: query the DOCUMENT record (and DOCUMENT_CHUNK count) from
        Cosmos DB via ``cosmos_service.get_document``.
        """

        return DocumentStatusResponse(
            document_id=document_id,
            status="PROCESSING",
            chunk_count=0,
            indexed_at=None,
        )

    async def delete_document(self, document_id: str) -> None:
        """Delete a document, its blob, and its search index entries.

        TODO: delete the blob (``storage_service.delete_blob``), the search
        index entries (``search_service.delete_document_chunks``), and the
        DOCUMENT/DOCUMENT_CHUNK Cosmos DB records
        (``cosmos_service.delete_document``).
        """

        logger.info("Stub delete accepted for document_id=%s", document_id)
