"""Configurable approval workflow engine.

Addresses IFS complaints:
- "No automatic approval routines in the system"
- "Permission workflow doesn't make sense, must manually create one for every situation"
- "Becomes very rigid in terms of customization"

Provides reusable, multi-step approval chains that can be attached to any entity
(ECR, ECO, product phase gate, document release).
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
    DELEGATED = "delegated"


class ApprovalTemplate(Base):
    """Reusable workflow template defining an ordered set of approval steps.

    Templates can be attached to entity types (e.g. "ecr_approval", "phase_gate",
    "document_release") so users don't need to create workflows from scratch.
    """

    __tablename__ = "approval_templates"

    name: Mapped[str] = mapped_column(String(200), unique=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(default=True)

    steps: Mapped[list["ApprovalTemplateStep"]] = relationship(
        back_populates="template", cascade="all, delete-orphan",
        order_by="ApprovalTemplateStep.step_order"
    )

    def __repr__(self) -> str:
        return f"<ApprovalTemplate '{self.name}'>"


class ApprovalTemplateStep(Base):
    """One step in a template — defines role/person and order."""

    __tablename__ = "approval_template_steps"

    template_id: Mapped[str] = mapped_column(ForeignKey("approval_templates.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(100))  # e.g. "design_lead", "quality_engineer"
    approver: Mapped[str] = mapped_column(String(200), default="")  # specific person or empty for role-based
    is_required: Mapped[bool] = mapped_column(default=True)
    auto_approve_after_hours: Mapped[int] = mapped_column(Integer, default=0)  # 0 = no auto-approve

    template: Mapped["ApprovalTemplate"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<ApprovalTemplateStep order={self.step_order} role='{self.role}'>"


class ApprovalRequest(Base):
    """A live approval workflow instance tied to a specific entity."""

    __tablename__ = "approval_requests"

    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("approval_templates.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300))
    current_step: Mapped[int] = mapped_column(Integer, default=1)
    is_complete: Mapped[bool] = mapped_column(default=False)
    is_approved: Mapped[bool] = mapped_column(default=False)

    decisions: Mapped[list["ApprovalDecision"]] = relationship(
        back_populates="request", cascade="all, delete-orphan",
        order_by="ApprovalDecision.step_order"
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest {self.entity_type}:{self.entity_id} step={self.current_step}>"


class ApprovalDecision(Base):
    """Individual approver's decision within an approval request."""

    __tablename__ = "approval_decisions"

    request_id: Mapped[str] = mapped_column(ForeignKey("approval_requests.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(100))
    decided_by: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), default=ApprovalStatus.PENDING
    )
    comment: Mapped[str] = mapped_column(Text, default="")

    request: Mapped["ApprovalRequest"] = relationship(back_populates="decisions")

    def __repr__(self) -> str:
        return f"<ApprovalDecision step={self.step_order} [{self.status.value}]>"
