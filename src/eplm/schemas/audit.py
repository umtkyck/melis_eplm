"""Pydantic schemas for audit trail."""

from datetime import datetime

from pydantic import BaseModel

from eplm.models.audit import AuditAction


class AuditLogResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: AuditAction
    actor: str
    summary: str
    old_values: str
    new_values: str
    created_at: datetime

    model_config = {"from_attributes": True}
