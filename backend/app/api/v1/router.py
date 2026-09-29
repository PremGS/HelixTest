"""Aggregates all API v1 routers."""

from fastapi import APIRouter

from app.api.v1 import audit, conversations, documents, health, queries

router = APIRouter()

router.include_router(health.router)
router.include_router(documents.router)
router.include_router(queries.router)
router.include_router(audit.router)
router.include_router(conversations.router)
