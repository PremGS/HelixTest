"""Audit trail endpoint.

Implements ``GET /audit/trail`` from the Key Endpoints list, matching the
Audit Trail Retrieval with RBAC Enforcement sequence diagram in
``.helix/ARCHITECTURE.md``. Gated to ``compliance_admin`` / ``system_admin``
roles.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from app.dependencies import require_role
from app.models.schemas import AuditTrailResponse, User

router = APIRouter(prefix="/audit", tags=["audit"])

_ALLOWED_ROLES = ("compliance_admin", "system_admin")


@router.get("/trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    from_: Optional[datetime] = None,
    to: Optional[datetime] = None,
    page: int = 1,
    limit: int = 50,
    user: User = Depends(require_role(*_ALLOWED_ROLES)),
) -> AuditTrailResponse:
    """Return a paginated, RBAC-gated audit trail.

    Access is restricted to users with the ``compliance_admin`` or
    ``system_admin`` CATS role claim (enforced by ``require_role`` above); the
    real APIM layer would also enforce this coarsely at the gateway.

    TODO: replace this stubbed empty page with a real call to
    ``CosmosService.query_audit_log``, filtering the ``audit_log`` container
    by date range, paginated and ordered by ``timestamp DESC``, and record
    this retrieval itself as a new AUDIT_LOG entry.
    """

    return AuditTrailResponse(entries=[], total_count=0, page=page, limit=limit)
