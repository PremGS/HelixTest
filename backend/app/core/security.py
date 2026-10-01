"""JWT validation helpers for CATS SSO OIDC tokens.

In the real architecture, JWT validation happens primarily at the Azure API
Management gateway boundary, with fine-grained RBAC re-checked here at the
FastAPI service layer (see "Security Considerations" in
``.helix/ARCHITECTURE.md``). This module stubs that fine-grained check.
"""

from __future__ import annotations

from typing import Any, Optional

from jose import jwt
from jose.exceptions import JWTError

from app.config import Settings, get_settings


class InvalidTokenError(Exception):
    """Raised when a CATS SSO token fails validation."""


def decode_token(token: str, settings: Optional[Settings] = None) -> dict[str, Any]:
    """Decode and validate a CATS SSO OIDC JWT.

    TODO: replace this stub with real signature verification against the
    CATS SSO JWKS endpoint (``settings.cats_sso_jwks_url``), checking
    ``iss``/``aud``/``exp`` claims. For local development/testing this
    currently decodes the token *without* verifying the signature so the
    rest of the stack can be exercised without a live CATS SSO instance.
    """

    settings = settings or get_settings()

    if settings.environment != "local":
        # Fail safe rather than silently trusting unverified claims outside
        # of local development. TODO: remove this guard once real JWKS-based
        # signature verification (below) is implemented for all environments.
        raise InvalidTokenError(
            "Unverified token decoding is only permitted when environment == 'local'; "
            "implement real CATS SSO JWKS signature verification for this environment."
        )

    try:
        # NOTE: signature verification intentionally disabled in this
        # scaffold. Do not use this as-is in a production deployment.
        claims = jwt.get_unverified_claims(token)
    except JWTError as exc:  # pragma: no cover - defensive
        raise InvalidTokenError("Could not decode token") from exc

    return claims


def get_role_claim(claims: dict[str, Any]) -> Optional[str]:
    """Extract the CATS RBAC role claim from decoded token claims."""

    return claims.get("role")
