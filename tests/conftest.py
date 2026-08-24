# Shared pytest configuration for TS-003 and broader test suite
# Configures asyncio mode, environment validation, and shared markers

import os
import pytest


def pytest_configure(config):
    """Register custom markers used across test suites."""
    config.addinivalue_line("markers", "smoke: fast smoke tests for CI gate")
    config.addinivalue_line("markers", "integration: tests requiring live services")
    config.addinivalue_line("markers", "e2e: full end-to-end browser tests")
    config.addinivalue_line("markers", "ts003: tests belonging to TS-003 suite")


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """
    Session-scoped fixture that warns (does not fail) if required
    environment variables are missing — allows local runs with defaults.
    """
    required_vars = ["API_BASE_URL", "TEST_AUTH_TOKEN"]
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        import warnings
        warnings.warn(
            f"Missing env vars (using defaults): {missing}. "
            "Set these in GitHub Actions secrets for CI runs.",
            UserWarning,
            stacklevel=2,
        )
