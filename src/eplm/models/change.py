"""Engineering Change Request (ECR) and Engineering Change Order (ECO) models."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class ChangeRequestStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ChangeOrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ChangeImpact(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeRequest(Base):
    """Engineering Change Request — proposes a change to a product or component.

    An ECR must be approved before an ECO can be created to implement the change.
    """

    __tablename__ = "change_requests"

    ecr_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    impact: Mapped[ChangeImpact] = mapped_column(
        Enum(ChangeImpact), default=ChangeImpact.MEDIUM
    )
    status: Mapped[ChangeRequestStatus] = mapped_column(
        Enum(ChangeRequestStatus), default=ChangeRequestStatus.DRAFT
    )
    requested_by: Mapped[str] = mapped_column(String(200), default="")
    reviewed_by: Mapped[str] = mapped_column(String(200), default="")
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("products.id"), nullable=True, index=True
    )

    change_orders: Mapped[list["ChangeOrder"]] = relationship(
        back_populates="change_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ECR {self.ecr_number} [{self.status.value}]>"


class ChangeOrder(Base):
    """Engineering Change Order — implements an approved change request.

    Tracks what items are affected and the implementation status.
    """

    __tablename__ = "change_orders"

    eco_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    change_request_id: Mapped[str] = mapped_column(
        ForeignKey("change_requests.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ChangeOrderStatus] = mapped_column(
        Enum(ChangeOrderStatus), default=ChangeOrderStatus.DRAFT
    )
    assigned_to: Mapped[str] = mapped_column(String(200), default="")
    approved_by: Mapped[str] = mapped_column(String(200), default="")
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    change_request: Mapped["ChangeRequest"] = relationship(back_populates="change_orders")
    items: Mapped[list["ChangeOrderItem"]] = relationship(
        back_populates="change_order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ECO {self.eco_number} [{self.status.value}]>"


class ChangeOrderItem(Base):
    """A single affected item within an ECO (component or product)."""

    __tablename__ = "change_order_items"

    change_order_id: Mapped[str] = mapped_column(
        ForeignKey("change_orders.id"), index=True
    )
    item_type: Mapped[str] = mapped_column(String(20))  # "product" or "component"
    item_id: Mapped[str] = mapped_column(String(36))
    from_revision: Mapped[str] = mapped_column(String(10), default="")
    to_revision: Mapped[str] = mapped_column(String(10), default="")
    change_description: Mapped[str] = mapped_column(Text, default="")

    change_order: Mapped["ChangeOrder"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"<ChangeOrderItem {self.item_type}:{self.item_id}>"
