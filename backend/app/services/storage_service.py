"""Stub wrapper around the Azure Blob Storage client (async).

See the "Azure Blob Storage" component in ``.helix/ARCHITECTURE.md``: durable
object storage for raw uploaded documents, processed artifacts, and export
outputs.
"""

from __future__ import annotations

from app.config import get_settings


class StorageService:
    """Thin async wrapper around ``azure.storage.blob.aio.BlobServiceClient``."""

    def __init__(self) -> None:
        self._settings = get_settings()
        # TODO: instantiate azure.storage.blob.aio.BlobServiceClient using
        # Managed Identity (DefaultAzureCredential) in real deployments,
        # falling back to a connection string for local dev only.
        self._client = None

    async def upload_blob(self, container: str, blob_name: str, data: bytes) -> str:
        """Upload raw bytes to ``container/blob_name`` and return the blob URI.

        TODO: stream ``data`` via ``BlobClient.upload_blob`` and return the
        resulting blob URI + ETag.
        """

        raise NotImplementedError("StorageService.upload_blob is not implemented")

    async def download_blob(self, container: str, blob_name: str) -> bytes:
        """Download the contents of a blob.

        TODO: use ``BlobClient.download_blob`` to stream bytes back.
        """

        raise NotImplementedError("StorageService.download_blob is not implemented")

    async def delete_blob(self, container: str, blob_name: str) -> None:
        """Delete a blob (used when a document is removed).

        TODO: use ``BlobClient.delete_blob``.
        """

        raise NotImplementedError("StorageService.delete_blob is not implemented")
