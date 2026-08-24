# TS-001: Shared pytest configuration for Authentication & Authorization tests
# STORY-2

import pytest
import os


def pytest_configure(config):
    """Register custom markers for TS-001 test suite."""
    config.addinivalue_line("markers", "auth: Authentication and authorization tests")
    config.addinivalue_line("markers", "rbac: Role-based access control tests")
    config.addinivalue_line("markers", "session: Session management tests")
    config.addinivalue_line("markers", "sso: SSO federation tests")
    config.addinivalue_line("markers", "security: Security boundary and negative tests")


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return the base URL for the API under test."""
    return os.getenv("API_BASE_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def azure_ad_b2c_config() -> dict:
    """Return Azure AD B2C configuration for the test session."""
    return {
        "tenant": os.getenv("AZURE_AD_B2C_TENANT", "test-tenant"),
        "client_id": os.getenv("AZURE_AD_B2C_CLIENT_ID", "test-client-id"),
        "issuer": os.getenv(
            "AZURE_AD_B2C_ISSUER",
            "https://test-tenant.b2clogin.com/test-tenant.onmicrosoft.com/v2.0/"
        ),
        "jwks_uri": os.getenv(
            "JWKS_URI",
            "https://test-tenant.b2clogin.com/test-tenant.onmicrosoft.com/discovery/v2.0/keys"
        ),
        "test_secret": os.getenv("TEST_JWT_SECRET", "test-secret-key-for-ci-only"),
    }
