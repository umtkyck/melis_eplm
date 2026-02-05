"""Audit trail API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.audit import AuditLogResponse
from eplm.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


def _svc(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(db)


@router.get("/history/{entity_type}/{entity_id}", response_model=list[AuditLogResponse])
async def entity_history(
    entity_type: str,
    entity_id: str,
    limit: int = Query(100, ge=1, le=500),
    svc: AuditService = Depends(_svc),
):
    return await svc.get_history(entity_type, entity_id, limit=limit)


@router.get("/recent", response_model=list[AuditLogResponse])
async def recent_activity(
    limit: int = Query(50, ge=1, le=200),
    svc: AuditService = Depends(_svc),
):
    return await svc.get_recent(limit=limit)


@router.get("/actor/{actor}", response_model=list[AuditLogResponse])
async def activity_by_actor(
    actor: str,
    limit: int = Query(50, ge=1, le=200),
    svc: AuditService = Depends(_svc),
):
    return await svc.get_by_actor(actor, limit=limit)
