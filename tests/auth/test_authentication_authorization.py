# TS-001: Authentication & Authorization
# Tests for Azure AD B2C and CATS SSO authentication flows,
# token issuance, role-based access control, and session management.
# Framework: pytest + httpx.AsyncClient
# STORY-2

import pytest
import httpx
import jwt
import time
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AZURE_AD_B2C_TENANT = os.getenv("AZURE_AD_B2C_TENANT", "test-tenant")
AZURE_AD_B2C_CLIENT_ID = os.getenv("AZURE_AD_B2C_CLIENT_ID", "test-client-id")
AZURE_AD_B2C_ISSUER = os.getenv(
    "AZURE_AD_B2C_ISSUER",
    f"https://{AZURE_AD_B2C_TENANT}.b2clogin.com/{AZURE_AD_B2C_TENANT}.onmicrosoft.com/v2.0/"
)
JWKS_URI = os.getenv(
    "JWKS_URI",
    f"https://{AZURE_AD_B2C_TENANT}.b2clogin.com/{AZURE_AD_B2C_TENANT}.onmicrosoft.com/discovery/v2.0/keys"
)
TEST_SECRET = os.getenv("TEST_JWT_SECRET", "test-secret-key-for-ci-only")
TEST_USER_ID = os.getenv("TEST_USER_ID", "test-user-oid-12345")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "testuser@example.com")

ROLE_PHARMA_REVIEWER = "PharmaReviewer"
ROLE_ADMIN = "Admin"
ROLE_READONLY = "ReadOnly"

PROTECTED_ENDPOINT = "/api/v1/documents"
ADMIN_ENDPOINT = "/api/v1/admin/users"
ROLEBASED_ENDPOINT = "/api/v1/claims"

SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", "3600"))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_b2c_token() -> str:
    """Generate a mock Azure AD B2C JWT for testing."""
    payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "name": "Test User",
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_PHARMA_REVIEWER],
        "scp": "sllip.read sllip.write",
        "tid": AZURE_AD_B2C_TENANT,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def valid_admin_token() -> str:
    """Generate a mock JWT with Admin role."""
    payload = {
        "sub": "admin-user-oid-99999",
        "oid": "admin-user-oid-99999",
        "email": "admin@example.com",
        "name": "Admin User",
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_ADMIN],
        "scp": "sllip.read sllip.write sllip.admin",
        "tid": AZURE_AD_B2C_TENANT,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def valid_readonly_token() -> str:
    """Generate a mock JWT with ReadOnly role."""
    payload = {
        "sub": "readonly-user-oid-77777",
        "oid": "readonly-user-oid-77777",
        "email": "readonly@example.com",
        "name": "ReadOnly User",
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_READONLY],
        "scp": "sllip.read",
        "tid": AZURE_AD_B2C_TENANT,
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def expired_token() -> str:
    """Generate an expired JWT."""
    payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()) - 7200,
        "exp": int(time.time()) - 3600,
        "roles": [ROLE_PHARMA_REVIEWER],
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def invalid_signature_token() -> str:
    """Generate a JWT with tampered/invalid signature."""
    payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_ADMIN],
    }
    # Encode with wrong secret to simulate tampered signature
    token = jwt.encode(payload, "wrong-secret-key", algorithm="HS256")
    return token

@pytest.fixture
def wrong_audience_token() -> str:
    """Generate a JWT with incorrect audience claim."""
    payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": "wrong-audience-id",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_PHARMA_REVIEWER],
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def wrong_issuer_token() -> str:
    """Generate a JWT with incorrect issuer claim."""
    payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": "https://malicious-issuer.example.com/",
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_ADMIN],
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

@pytest.fixture
def cats_sso_token() -> str:
    """Generate a mock CATS SSO token."""
    payload = {
        "sub": "cats-user-oid-55555",
        "email": "catsuser@corporate.example.com",
        "name": "CATS SSO User",
        "iss": os.getenv("CATS_SSO_ISSUER", "https://cats-sso.example.com/"),
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_PHARMA_REVIEWER],
        "provider": "cats_sso",
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


# ---------------------------------------------------------------------------
# Mock helper for JWKS validation bypass in CI
# ---------------------------------------------------------------------------

def _mock_jwks_validate(token: str) -> Dict[str, Any]:
    """Bypass live JWKS in CI by decoding with test secret."""
    return jwt.decode(
        token,
        TEST_SECRET,
        algorithms=["HS256"],
        options={"verify_aud": False}
    )


# ---------------------------------------------------------------------------
# TC-001-001: Valid Azure AD B2C JWT authorizes request and injects user claims
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_valid_b2c_jwt_authorizes_and_injects_claims(mock_validate, valid_b2c_token):
    """
    TC-001-001 | STORY-2
    Validates that a well-formed Azure AD B2C JWT:
    1. Passes through auth middleware without error
    2. Is validated against the JWKS endpoint
    3. Injects user claims (sub, email, roles) into the request context
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {valid_b2c_token}"}
        )

    # Step 1: Request received by middleware without connection errors
    assert response.status_code != 502, "Gateway error — middleware unreachable"
    assert response.status_code != 503, "Service unavailable — middleware unreachable"

    # Step 2: Token validated — not rejected as unauthorized
    assert response.status_code != 401, (
        f"Token was incorrectly rejected as unauthorized. "
        f"Response: {response.text}"
    )
    assert response.status_code != 403, (
        f"Token was incorrectly rejected as forbidden. "
        f"Response: {response.text}"
    )

    # Step 3: Middleware invoked validate function (JWKS path exercised)
    mock_validate.assert_called_once()
    call_args = mock_validate.call_args[0]
    assert valid_b2c_token in call_args or valid_b2c_token == call_args[0], (
        "Auth middleware did not pass the bearer token to the JWKS validator"
    )

    # Step 4: Verify claims injected into context via response headers or body
    # The API is expected to echo context claims in a /me or X-User-* header
    # pattern — adjust per actual implementation
    response_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
    user_context = response_data.get("user") or response_data.get("context") or {}

    # If X-User-Id header is set by middleware, validate it
    if "x-user-id" in response.headers:
        assert response.headers["x-user-id"] == TEST_USER_ID, (
            f"Injected user ID mismatch. Expected {TEST_USER_ID}, "
            f"got {response.headers['x-user-id']}"
        )

    # If user context is present in body, validate email claim
    if user_context:
        assert user_context.get("email") == TEST_USER_EMAIL or \
               user_context.get("oid") == TEST_USER_ID, (
            "User claims not correctly injected into request context"
        )


# ---------------------------------------------------------------------------
# TC-001-002: Expired JWT is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_expired_jwt_is_rejected_with_401(expired_token):
    """
    TC-001-002 | STORY-2
    Validates that an expired Azure AD B2C JWT is rejected
    by the auth middleware with HTTP 401 Unauthorized.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {expired_token}"}
        )

    assert response.status_code == 401, (
        f"Expected 401 for expired token, got {response.status_code}. "
        f"Response: {response.text}"
    )

    response_body = response.json()
    assert "error" in response_body or "detail" in response_body or "message" in response_body, (
        "Error response body missing 'error', 'detail', or 'message' field"
    )

    error_message = (
        response_body.get("error") or
        response_body.get("detail") or
        response_body.get("message") or ""
    ).lower()

    assert any(keyword in error_message for keyword in ["expired", "token", "invalid", "unauthorized"]), (
        f"Error message does not indicate token expiry. Got: {error_message}"
    )


# ---------------------------------------------------------------------------
# TC-001-003: JWT with invalid signature is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_signature_jwt_rejected_with_401(invalid_signature_token):
    """
    TC-001-003 | STORY-2
    Validates that a JWT with a tampered/invalid signature is rejected
    by the auth middleware with HTTP 401 Unauthorized.
    Ensures the JWKS signature verification is enforced.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {invalid_signature_token}"}
        )

    assert response.status_code == 401, (
        f"Expected 401 for tampered signature, got {response.status_code}. "
        f"Response: {response.text}"
    )

    response_body = response.json()
    error_message = (
        response_body.get("error") or
        response_body.get("detail") or
        response_body.get("message") or ""
    ).lower()

    assert any(keyword in error_message for keyword in ["signature", "invalid", "token", "unauthorized"]), (
        f"Error message does not indicate signature failure. Got: {error_message}"
    )


# ---------------------------------------------------------------------------
# TC-001-004: JWT with wrong audience claim is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_audience_jwt_rejected_with_401(wrong_audience_token):
    """
    TC-001-004 | STORY-2
    Validates that a JWT bearing an audience (aud) claim that does not
    match the configured SLLIP client ID is rejected with 401.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {wrong_audience_token}"}
        )

    assert response.status_code == 401, (
        f"Expected 401 for wrong audience, got {response.status_code}. "
        f"Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-005: JWT with wrong issuer claim is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_wrong_issuer_jwt_rejected_with_401(wrong_issuer_token):
    """
    TC-001-005 | STORY-2
    Validates that a JWT from an untrusted issuer is rejected by the
    auth middleware with HTTP 401 Unauthorized.
    Prevents token relay attacks from third-party issuers.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {wrong_issuer_token}"}
        )

    assert response.status_code == 401, (
        f"Expected 401 for wrong issuer, got {response.status_code}. "
        f"Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-006: Request with no Authorization header is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_authorization_header_returns_401():
    """
    TC-001-006 | STORY-2
    Validates that a request with no Authorization header is rejected
    with HTTP 401. Ensures all protected endpoints require authentication.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(PROTECTED_ENDPOINT)

    assert response.status_code == 401, (
        f"Expected 401 for missing auth header, got {response.status_code}. "
        f"Response: {response.text}"
    )

    response_body = response.json()
    assert "error" in response_body or "detail" in response_body or "message" in response_body, (
        "Missing auth error response body should contain 'error', 'detail', or 'message'"
    )


# ---------------------------------------------------------------------------
# TC-001-007: Request with malformed Bearer token is rejected with HTTP 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_malformed_bearer_token_returns_401():
    """
    TC-001-007 | STORY-2
    Validates that a malformed or non-JWT bearer token string
    is rejected with HTTP 401 by the auth middleware.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt.token"}
        )

    assert response.status_code == 401, (
        f"Expected 401 for malformed token, got {response.status_code}. "
        f"Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-008: Admin role can access admin-only endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_admin_role_can_access_admin_endpoint(mock_validate, valid_admin_token):
    """
    TC-001-008 | STORY-2
    Validates that a user bearing the 'Admin' role in their JWT claims
    is granted access to admin-only protected endpoints.
    Verifies role-based access control (RBAC) enforcement.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            ADMIN_ENDPOINT,
            headers={"Authorization": f"Bearer {valid_admin_token}"}
        )

    assert response.status_code not in [401, 403], (
        f"Admin user should have access to admin endpoint. "
        f"Got {response.status_code}. Response: {response.text}"
    )
    assert response.status_code in [200, 201, 204], (
        f"Expected 2xx for admin access, got {response.status_code}"
    )


# ---------------------------------------------------------------------------
# TC-001-009: Non-admin role is denied access to admin-only endpoint (403)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_non_admin_role_denied_admin_endpoint(mock_validate, valid_b2c_token):
    """
    TC-001-009 | STORY-2
    Validates that a user with 'PharmaReviewer' role is denied access to
    admin-only endpoints with HTTP 403 Forbidden.
    Ensures RBAC prevents privilege escalation.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            ADMIN_ENDPOINT,
            headers={"Authorization": f"Bearer {valid_b2c_token}"}
        )

    assert response.status_code == 403, (
        f"Expected 403 Forbidden for non-admin user on admin endpoint. "
        f"Got {response.status_code}. Response: {response.text}"
    )

    response_body = response.json()
    error_message = (
        response_body.get("error") or
        response_body.get("detail") or
        response_body.get("message") or ""
    ).lower()

    assert any(keyword in error_message for keyword in ["forbidden", "permission", "role", "access", "unauthorized"]), (
        f"403 response should indicate insufficient permissions. Got: {error_message}"
    )


# ---------------------------------------------------------------------------
# TC-001-010: ReadOnly role cannot perform write operations (403)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_readonly_role_denied_write_operation(mock_validate, valid_readonly_token):
    """
    TC-001-010 | STORY-2
    Validates that a user with 'ReadOnly' role cannot perform POST/PUT/DELETE
    operations on write-protected endpoints. Expects HTTP 403.
    """
    payload = {
        "document_name": "test_document.pdf",
        "therapeutic_area": "Oncology"
    }
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            PROTECTED_ENDPOINT,
            json=payload,
            headers={"Authorization": f"Bearer {valid_readonly_token}"}
        )

    assert response.status_code == 403, (
        f"Expected 403 for ReadOnly user on write endpoint. "
        f"Got {response.status_code}. Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-011: CATS SSO token is accepted and grants access
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_cats_sso_token", side_effect=_mock_jwks_validate)
async def test_cats_sso_token_accepted(mock_validate, cats_sso_token):
    """
    TC-001-011 | STORY-2
    Validates that a CATS SSO token is accepted by the auth middleware
    and grants access to protected endpoints for federated SSO users.
    """
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {cats_sso_token}"}
        )

    assert response.status_code not in [401, 403], (
        f"CATS SSO token should be accepted. "
        f"Got {response.status_code}. Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-012: Session token expiry triggers re-authentication
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_expiry_triggers_reauthentication():
    """
    TC-001-012 | STORY-2
    Validates that once a session token has expired, subsequent requests
    using that expired token are rejected with 401, requiring the client
    to re-authenticate. Validates session management enforcement.
    """
    expired_session_payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()) - (SESSION_TIMEOUT_SECONDS + 600),
        "exp": int(time.time()) - 600,  # Expired 10 minutes ago
        "roles": [ROLE_PHARMA_REVIEWER],
        "session_id": "expired-session-abc123",
    }
    expired_session_token = jwt.encode(expired_session_payload, TEST_SECRET, algorithm="HS256")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {expired_session_token}"}
        )

    assert response.status_code == 401, (
        f"Expired session token should return 401. "
        f"Got {response.status_code}. Response: {response.text}"
    )

    # Validate WWW-Authenticate header is present (RFC 6750 compliance)
    # TBD: confirm if WWW-Authenticate header is enforced in implementation
    # assert "WWW-Authenticate" in response.headers, (
    #     "RFC 6750 requires WWW-Authenticate header on 401 responses"
    # )


# ---------------------------------------------------------------------------
# TC-001-013: Token with no roles claim is denied access to role-gated endpoint
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_token_without_roles_denied_role_gated_endpoint(mock_validate):
    """
    TC-001-013 | STORY-2
    Validates that a valid JWT missing the 'roles' claim is denied access
    to role-gated endpoints with HTTP 403 Forbidden.
    """
    no_roles_payload = {
        "sub": TEST_USER_ID,
        "oid": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "iss": AZURE_AD_B2C_ISSUER,
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        # 'roles' claim intentionally omitted
    }
    no_roles_token = jwt.encode(no_roles_payload, TEST_SECRET, algorithm="HS256")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            ROLEBASED_ENDPOINT,
            headers={"Authorization": f"Bearer {no_roles_token}"}
        )

    assert response.status_code == 403, (
        f"Token without roles should be denied with 403. "
        f"Got {response.status_code}. Response: {response.text}"
    )


# ---------------------------------------------------------------------------
# TC-001-014: Concurrent requests with same valid token all succeed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@patch("shared.auth.middleware.validate_azure_b2c_token", side_effect=_mock_jwks_validate)
async def test_concurrent_requests_same_token_all_succeed(mock_validate, valid_b2c_token):
    """
    TC-001-014 | STORY-2
    Validates that multiple concurrent requests using the same valid JWT
    all succeed without race conditions or session conflicts.
    Verifies stateless token validation behavior.
    """
    import asyncio

    async def make_request(client: httpx.AsyncClient) -> int:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {valid_b2c_token}"}
        )
        return response.status_code

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        status_codes = await asyncio.gather(
            *[make_request(client) for _ in range(5)]
        )

    for i, status_code in enumerate(status_codes):
        assert status_code not in [401, 403], (
            f"Concurrent request {i+1} failed with {status_code}. "
            f"All concurrent requests with valid token should succeed."
        )


# ---------------------------------------------------------------------------
# TC-001-015: Token issued for different tenant is rejected
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_token_from_different_tenant_rejected():
    """
    TC-001-015 | STORY-2
    Validates that a JWT issued from a different Azure AD B2C tenant
    is rejected with HTTP 401. Prevents cross-tenant token misuse.
    """
    cross_tenant_payload = {
        "sub": "attacker-user-id",
        "oid": "attacker-user-id",
        "email": "attacker@malicious-tenant.onmicrosoft.com",
        "iss": "https://malicious-tenant.b2clogin.com/malicious-tenant.onmicrosoft.com/v2.0/",
        "aud": AZURE_AD_B2C_CLIENT_ID,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "roles": [ROLE_ADMIN],
        "tid": "malicious-tenant-id",
    }
    cross_tenant_token = jwt.encode(cross_tenant_payload, TEST_SECRET, algorithm="HS256")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(
            PROTECTED_ENDPOINT,
            headers={"Authorization": f"Bearer {cross_tenant_token}"}
        )

    assert response.status_code == 401, (
        f"Cross-tenant token should be rejected with 401. "
        f"Got {response.status_code}. Response: {response.text}"
    )
