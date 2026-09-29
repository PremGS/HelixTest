"""Shared FastAPI dependencies."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status

from app.core.security import InvalidTokenError, decode_token, get_role_claim
from app.models.schemas import User


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> User:
    """Validate the ``Authorization`` bearer token and resolve the current user.

    This is a stub for the real CATS SSO integration: Azure API Management is
    expected to have already validated the token at the gateway boundary, but
    the FastAPI service layer re-validates and extracts user/role claims for
    fine-grained RBAC decisions (see ``.helix/ARCHITECTURE.md`` Security
    Considerations).

    TODO: replace with real claim extraction (sub, email, department, etc.)
    once CATS SSO integration is implemented.
    """

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header",
        )

    token = authorization.split(" ", 1)[1]

    try:
        claims = decode_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    role = get_role_claim(claims)
    if not role:
        # Since signatures aren't verified yet (see ``core.security``), we
        # deliberately do not fall back to a default role here: a forged or
        # incomplete token must not be able to silently obtain a role by
        # simply omitting the claim.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing a required role claim",
        )

    # TODO: populate this from real claims / a Cosmos DB user lookup. The
    # ``created_at`` claim (if CATS ever sends one) is not currently parsed
    # since its format is unspecified for this scaffold; we default to "now"
    # to keep the stub ``User`` construction well-typed.
    return User(
        id=claims.get("sub", "stub-user-id"),
        email=claims.get("email", "stub-user@example.com"),
        display_name=claims.get("name", "Stub User"),
        role=role,
        department=claims.get("department"),
        created_at=_now(),
        is_active=True,
    )


def require_role(*allowed_roles: str):
    """Return a dependency that enforces the current user has one of ``allowed_roles``.

    Used to gate RBAC-sensitive endpoints such as ``GET /api/v1/audit/trail``.
    """

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient RBAC role for this operation",
            )
        return user

    return _checker


def _now():
    return datetime.now(timezone.utc)
