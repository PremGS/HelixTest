# TS-003: Document Upload & Format Validation
# Framework: pytest + httpx.AsyncClient
# Stack: Python 3.11 / FastAPI backend on Azure Container Apps

import io
import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
AUTH_TOKEN = os.environ.get("TEST_AUTH_TOKEN", "test-jwt-token-legal-reviewer")

AUTH_HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
}


@pytest.fixture
def valid_pdf_bytes():
    """Minimal valid PDF binary fixture."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )


@pytest.fixture
def valid_docx_bytes():
    """Minimal DOCX-like binary fixture (ZIP magic bytes)."""
    return b"PK\x03\x04" + b"\x00" * 256


@pytest.fixture
def oversized_pdf_bytes():
    """Simulate a file exceeding 50 MB upload limit."""
    return b"%PDF-1.4\n" + b"A" * (51 * 1024 * 1024)


# ---------------------------------------------------------------------------
# TC-003-001: Successful upload of a valid PDF pharmaceutical document
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_pdf_upload(valid_pdf_bytes):
    """
    TC-003-001 | STORY-001 | STORY-7
    Verifies that an authenticated Legal Reviewer can upload a valid PDF
    pharmaceutical document and receive a confirmed upload response with
    a document ID and Azure Blob Storage reference.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": ("clinical_trial_report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
        }
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code == 201, (
        f"Expected 201 Created, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "document_id" in body, "Response must contain 'document_id'"
    assert "blob_url" in body or "storage_reference" in body, (
        "Response must contain Azure Blob storage reference"
    )
    assert body.get("status") in ("uploaded", "processing", "queued"), (
        f"Unexpected status value: {body.get('status')}"
    )
    assert body.get("filename") == "clinical_trial_report.pdf", (
        "Filename in response does not match uploaded file"
    )


# ---------------------------------------------------------------------------
# TC-003-002: Upload rejected for unsupported file format (e.g., .exe)
# STORY-001
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unsupported_file_format_rejected():
    """
    TC-003-002 | STORY-001
    Verifies that uploading an unsupported file type (e.g., .exe) returns
    HTTP 422 with a descriptive validation error and does NOT store the file.
    """
    fake_exe_bytes = b"MZ\x90\x00" + b"\x00" * 64  # PE header magic bytes
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": ("malware.exe", io.BytesIO(fake_exe_bytes), "application/octet-stream")
        }
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code == 422, (
        f"Expected 422 Unprocessable Entity, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "detail" in body or "error" in body, "Error response must include detail/error field"
    error_message = str(body.get("detail", body.get("error", ""))).lower()
    assert any(kw in error_message for kw in ("format", "type", "unsupported", "invalid")), (
        f"Error message should reference file type issue, got: {error_message}"
    )


# ---------------------------------------------------------------------------
# TC-003-003: Upload rejected for oversized file exceeding limit
# STORY-001
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_oversized_file_upload_rejected(oversized_pdf_bytes):
    """
    TC-003-003 | STORY-001
    Verifies that a file exceeding the maximum allowed size (50 MB) is
    rejected with HTTP 413 and an appropriate error message.
    """
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=httpx.Timeout(60.0)
    ) as client:
        files = {
            "file": ("huge_document.pdf", io.BytesIO(oversized_pdf_bytes), "application/pdf")
        }
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code in (413, 422), (
        f"Expected 413 or 422 for oversized file, got {response.status_code}: {response.text}"
    )
    body = response.json()
    error_text = str(body.get("detail", body.get("error", ""))).lower()
    assert any(kw in error_text for kw in ("size", "large", "limit", "exceed")), (
        f"Error message should reference file size, got: {error_text}"
    )


# ---------------------------------------------------------------------------
# TC-003-004: Unauthenticated upload attempt returns 401
# STORY-001
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unauthenticated_upload_rejected(valid_pdf_bytes):
    """
    TC-003-004 | STORY-001
    Verifies that an upload attempt without a valid authentication token
    is rejected with HTTP 401 Unauthorized — enforcing CATS SSO/RBAC.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": ("clinical_trial_report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
        }
        # No Authorization header
        response = await client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 401, (
        f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-003-005: Upload with invalid/expired token returns 403
# STORY-001
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_token_upload_rejected(valid_pdf_bytes):
    """
    TC-003-005 | STORY-001
    Verifies that an upload attempt using an expired or invalid JWT token
    is rejected with HTTP 401 or 403, not silently accepted.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": ("clinical_trial_report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
        }
        headers = {"Authorization": "Bearer invalid.jwt.token.xyz"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code in (401, 403), (
        f"Expected 401/403 for invalid token, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-003-006: Successful upload of a valid DOCX pharmaceutical document
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_docx_upload(valid_docx_bytes):
    """
    TC-003-006 | STORY-001 | STORY-7
    Verifies that a valid .docx file is accepted by the upload endpoint
    and returns a 201 with document metadata — confirming multi-format support.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": (
                "regulatory_submission.docx",
                io.BytesIO(valid_docx_bytes),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code == 201, (
        f"Expected 201 Created for DOCX upload, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "document_id" in body, "Response must contain 'document_id' for DOCX upload"


# ---------------------------------------------------------------------------
# TC-003-007: Empty file upload is rejected with validation error
# STORY-001
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_empty_file_upload_rejected():
    """
    TC-003-007 | STORY-001
    Verifies that uploading a zero-byte file returns HTTP 422 with a
    validation error indicating the file is empty/invalid.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        files = {
            "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
        }
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        response = await client.post("/api/v1/documents/upload", files=files, headers=headers)

    assert response.status_code == 422, (
        f"Expected 422 for empty file, got {response.status_code}: {response.text}"
    )
    body = response.json()
    error_text = str(body.get("detail", body.get("error", ""))).lower()
    assert any(kw in error_text for kw in ("empty", "invalid", "content", "size")), (
        f"Error should reference empty/invalid file, got: {error_text}"
    )


# ---------------------------------------------------------------------------
# TC-003-008: Upload endpoint returns document_id usable for status polling
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_upload_response_document_id_is_pollable(valid_pdf_bytes):
    """
    TC-003-008 | STORY-001 | STORY-7
    Verifies that the document_id returned after a successful upload can
    be used to poll the document status endpoint, confirming end-to-end
    routing from upload to processing pipeline.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

        # Step 1: Upload
        files = {
            "file": ("clinical_trial_report.pdf", io.BytesIO(valid_pdf_bytes), "application/pdf")
        }
        upload_response = await client.post(
            "/api/v1/documents/upload", files=files, headers=headers
        )
        assert upload_response.status_code == 201, (
            f"Upload failed: {upload_response.status_code} {upload_response.text}"
        )
        document_id = upload_response.json().get("document_id")
        assert document_id, "document_id must be present in upload response"

        # Step 2: Poll status
        status_response = await client.get(
            f"/api/v1/documents/{document_id}/status", headers=headers
        )
        assert status_response.status_code == 200, (
            f"Status endpoint returned {status_response.status_code} for document_id={document_id}"
        )
        status_body = status_response.json()
        assert "status" in status_body, "Status response must contain 'status' field"
        assert status_body["status"] in (
            "uploaded", "queued", "processing", "completed", "failed"
        ), f"Unexpected processing status: {status_body['status']}"


# ---------------------------------------------------------------------------
# TC-003-009: Azure Blob Storage unavailability returns 503
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_azure_blob_unavailable_returns_503(valid_pdf_bytes):
    """
    TC-003-009 | STORY-001 | STORY-7
    Verifies that when Azure Blob Storage is unreachable, the upload
    endpoint returns HTTP 503 Service Unavailable with an error message,
    and does not return a partial/corrupt success response.
    NOTE: Uses mock to simulate Blob Storage failure in CI without
    requiring a live Azure environment.
    """
    with patch(
        "app.services.blob_storage.AzureBlobStorageService.upload_document",
        new_callable=AsyncMock,
        side_effect=Exception("Azure Blob Storage connection timeout"),
    ):
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            files = {
                "file": (
                    "clinical_trial_report.pdf",
                    io.BytesIO(valid_pdf_bytes),
                    "application/pdf",
                )
            }
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            response = await client.post(
                "/api/v1/documents/upload", files=files, headers=headers
            )

    assert response.status_code in (503, 500), (
        f"Expected 503/500 when Blob Storage unavailable, got {response.status_code}: {response.text}"
    )
    body = response.json()
    assert "detail" in body or "error" in body, (
        "Error response must include detail or error field for storage failure"
    )


# ---------------------------------------------------------------------------
# TC-003-010: Duplicate filename upload is handled gracefully
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_duplicate_filename_upload_handled(valid_pdf_bytes):
    """
    TC-003-010 | STORY-001 | STORY-7
    Verifies that uploading a file with the same filename as a previously
    uploaded document either creates a new versioned entry or returns a
    meaningful conflict/versioning response — not a silent overwrite.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
        file_payload = lambda: {
            "file": (
                "clinical_trial_report.pdf",
                io.BytesIO(valid_pdf_bytes),
                "application/pdf",
            )
        }

        # First upload
        first_response = await client.post(
            "/api/v1/documents/upload", files=file_payload(), headers=headers
        )
        assert first_response.status_code == 201, (
            f"First upload failed: {first_response.status_code}"
        )
        first_doc_id = first_response.json().get("document_id")

        # Second upload — same filename
        second_response = await client.post(
            "/api/v1/documents/upload", files=file_payload(), headers=headers
        )
        assert second_response.status_code in (201, 409), (
            f"Duplicate upload should return 201 (versioned) or 409 (conflict), "
            f"got {second_response.status_code}"
        )
        if second_response.status_code == 201:
            second_doc_id = second_response.json().get("document_id")
            assert second_doc_id != first_doc_id, (
                "Duplicate file must generate a distinct document_id"
            )
