"""Audit trail — immutable log of every entity change.

Addresses IFS complaint: no change history, no tracking of who changed what/when.
Every create, update, delete, and state transition is recorded.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    PHASE_TRANSITION = "phase_transition"
    STATUS_CHANGE = "status_change"
    APPROVAL = "approval"
    REJECTION = "rejection"
    REVISION_CREATED = "revision_created"
    BOM_CLONE = "bom_clone"
    LINE_ITEM_ADDED = "line_item_added"
    LINE_ITEM_REMOVED = "line_item_removed"


from eplm.models.base import Base


class AuditLog(Base):
    """Immutable audit entry. One row per action on any tracked entity."""

    __tablename__ = "audit_log"

    entity_type: Mapped[str] = mapped_column(String(50), index=True)  # "product", "component", etc.
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction))
    actor: Mapped[str] = mapped_column(String(200), default="system")
    summary: Mapped[str] = mapped_column(Text, default="")
    old_values: Mapped[str] = mapped_column(Text, default="")  # JSON snapshot of previous state
    new_values: Mapped[str] = mapped_column(Text, default="")  # JSON snapshot of new state

    def __repr__(self) -> str:
        return f"<AuditLog {self.entity_type}:{self.entity_id} {self.action.value}>"
