# TS-003: Document Upload & Format Validation — E2E Tests
# Framework: Playwright (Python) — headless Chromium in GitHub Actions
# Stack: React.js frontend + FastAPI backend on Azure Container Apps

import os
import pathlib
import tempfile
import pytest
from playwright.sync_api import Page, expect, sync_playwright

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "legal.reviewer@sllip-test.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "TestPassword123!")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context():
    """Session-scoped headless Chromium browser context for CI."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            accept_downloads=True,
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def authenticated_page(browser_context):
    """Provides a Playwright page pre-authenticated as Legal Reviewer."""
    page = browser_context.new_page()
    page.goto(f"{FRONTEND_URL}/login")
    page.fill("[data-testid='email-input']", TEST_USER_EMAIL)
    page.fill("[data-testid='password-input']", TEST_USER_PASSWORD)
    page.click("[data-testid='login-submit-btn']")
    expect(page).to_have_url(f"{FRONTEND_URL}/dashboard", timeout=15000)
    yield page
    page.close()


@pytest.fixture
def temp_pdf_file():
    """Creates a temporary valid PDF file for upload testing."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )
    with tempfile.NamedTemporaryFile(
        suffix=".pdf", prefix="clinical_trial_report_", delete=False
    ) as f:
        f.write(pdf_content)
        tmp_path = f.name
    yield tmp_path
    pathlib.Path(tmp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_invalid_file():
    """Creates a temporary .exe file for negative format testing."""
    with tempfile.NamedTemporaryFile(
        suffix=".exe", prefix="invalid_", delete=False
    ) as f:
        f.write(b"MZ" + b"\x00" * 64)
        tmp_path = f.name
    yield tmp_path
    pathlib.Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TC-003-001 (E2E): Successful upload of a valid PDF pharmaceutical document
# STORY-001, STORY-7
# ---------------------------------------------------------------------------
def test_e2e_successful_pdf_upload(authenticated_page: Page, temp_pdf_file: str):
    """
    TC-003-001 (E2E) | STORY-001 | STORY-7
    Full end-to-end verification: authenticated Legal Reviewer navigates to
    the upload page, selects a valid PDF, submits, and sees upload confirmation
    with a document reference rendered in the React UI.
    """
    page = authenticated_page

    # Step 1: Navigate to upload page
    page.goto(f"{FRONTEND_URL}/documents/upload")
    expect(page.locator("[data-testid='upload-page-heading']")).to_be_visible(timeout=10000)
    expect(page.locator("[data-testid='file-input']")).to_be_visible()
    expect(page.locator("[data-testid='upload-submit-btn']")).to_be_visible()

    # Step 2: Select a valid PDF file
    page.set_input_files("[data-testid='file-input']", temp_pdf_file)
    selected_filename = page.locator("[data-testid='selected-filename']").inner_text()
    assert "clinical_trial_report" in selected_filename.lower(), (
        f"Selected filename not displayed correctly: {selected_filename}"
    )

    # Step 3: Click the upload button
    page.click("[data-testid='upload-submit-btn']")

    # Step 4: Upload progress indicator appears
    expect(page.locator("[data-testid='upload-progress']")).to_be_visible(timeout=5000)

    # Step 5: Success confirmation is displayed
    expect(page.locator("[data-testid='upload-success-message']")).to_be_visible(timeout=30000)
    success_text = page.locator("[data-testid='upload-success-message']").inner_text()
    assert any(kw in success_text.lower() for kw in ("success", "uploaded", "complete")), (
        f"Success message text unexpected: {success_text}"
    )

    # Step 6: Document ID or reference is shown
    expect(page.locator("[data-testid='document-id']")).to_be_visible(timeout=10000)
    doc_id_text = page.locator("[data-testid='document-id']").inner_text()
    assert len(doc_id_text.strip()) > 0, "Document ID must be rendered after successful upload"


# ---------------------------------------------------------------------------
# TC-003-002 (E2E): Unsupported file format shows inline validation error
# STORY-001
# ---------------------------------------------------------------------------
def test_e2e_unsupported_format_shows_error(authenticated_page: Page, temp_invalid_file: str):
    """
    TC-003-002 (E2E) | STORY-001
    Verifies that selecting an unsupported file type (.exe) triggers
    an inline validation error message in the React UI before or after
    submit, and that no success state is rendered.
    """
    page = authenticated_page
    page.goto(f"{FRONTEND_URL}/documents/upload")
    expect(page.locator("[data-testid='upload-page-heading']")).to_be_visible(timeout=10000)

    page.set_input_files("[data-testid='file-input']", temp_invalid_file)
    page.click("[data-testid='upload-submit-btn']")

    # Error message must appear
    expect(page.locator("[data-testid='upload-error-message']")).to_be_visible(timeout=10000)
    error_text = page.locator("[data-testid='upload-error-message']").inner_text()
    assert any(kw in error_text.lower() for kw in ("format", "type", "unsupported", "invalid", "not allowed")), (
        f"Error message should reference file format, got: {error_text}"
    )

    # Success state must NOT be visible
    assert not page.locator("[data-testid='upload-success-message']").is_visible(), (
        "Success message must not appear after unsupported format upload"
    )


# ---------------------------------------------------------------------------
# TC-003-003 (E2E): Upload page is inaccessible without authentication
# STORY-001
# ---------------------------------------------------------------------------
def test_e2e_unauthenticated_redirected_to_login():
    """
    TC-003-003 (E2E) | STORY-001
    Verifies that an unauthenticated user attempting to access the document
    upload page is redirected to the login screen — enforcing CATS SSO/RBAC
    at the UI routing level.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"],
        )
        page = browser.new_page()
        page.goto(f"{FRONTEND_URL}/documents/upload")
        # Should be redirected to login
        expect(page).to_have_url(
            lambda url: "/login" in url or "/auth" in url,
            timeout=10000,
        )
        browser.close()


# ---------------------------------------------------------------------------
# TC-003-004 (E2E): File selection control displays selected filename
# STORY-001
# ---------------------------------------------------------------------------
def test_e2e_file_selection_displays_filename(authenticated_page: Page, temp_pdf_file: str):
    """
    TC-003-004 (E2E) | STORY-001
    Verifies that when a user selects a file via the file picker, the
    selected filename is rendered in the upload interface (UX confirmation
    before submission).
    """
    page = authenticated_page
    page.goto(f"{FRONTEND_URL}/documents/upload")
    expect(page.locator("[data-testid='upload-page-heading']")).to_be_visible(timeout=10000)

    page.set_input_files("[data-testid='file-input']", temp_pdf_file)

    filename_display = page.locator("[data-testid='selected-filename']")
    expect(filename_display).to_be_visible(timeout=5000)
    displayed_name = filename_display.inner_text()
    assert "clinical_trial_report" in displayed_name.lower(), (
        f"Filename display should show selected file name, got: {displayed_name}"
    )


# ---------------------------------------------------------------------------
# TC-003-005 (E2E): Upload progress indicator is shown during upload
# STORY-001
# ---------------------------------------------------------------------------
def test_e2e_upload_progress_indicator_visible(authenticated_page: Page, temp_pdf_file: str):
    """
    TC-003-005 (E2E) | STORY-001
    Verifies that after clicking Submit, an upload progress indicator
    (spinner, progress bar, or loading state) is rendered while the
    upload is in-flight — preventing duplicate submissions.
    """
    page = authenticated_page
    page.goto(f"{FRONTEND_URL}/documents/upload")
    expect(page.locator("[data-testid='upload-page-heading']")).to_be_visible(timeout=10000)

    page.set_input_files("[data-testid='file-input']", temp_pdf_file)
    page.click("[data-testid='upload-submit-btn']")

    # Progress indicator should appear immediately after submit
    progress_locator = page.locator(
        "[data-testid='upload-progress'], [data-testid='loading-spinner'], [role='progressbar']"
    )
    expect(progress_locator).to_be_visible(timeout=5000)
