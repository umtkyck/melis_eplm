"""Audit trail recording and querying.

Addresses IFS complaint: no visibility into who changed what and when.
Provides immutable, queryable history for every entity in the system.
"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.models.audit import AuditAction, AuditLog


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        actor: str = "system",
        summary: str = "",
        old_values: dict | None = None,
        new_values: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            summary=summary,
            old_values=json.dumps(old_values or {}, default=str),
            new_values=json.dumps(new_values or {}, default=str),
        )
        self.db.add(entry)
        # Don't commit here — caller controls the transaction
        return entry

    async def get_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(self, limit: int = 50) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_actor(self, actor: str, limit: int = 50) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.actor == actor)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
