"""Webhook/event notification system.

Addresses IFS complaint: "Integration options with third-party solutions are limited."

Provides an event-driven integration layer so external systems (CAD tools, ERP,
test automation, notification services) can subscribe to PLM events.
"""

import enum

from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from eplm.models.base import Base


class WebhookEvent(str, enum.Enum):
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_PHASE_CHANGED = "product.phase_changed"
    COMPONENT_CREATED = "component.created"
    COMPONENT_UPDATED = "component.updated"
    BOM_CREATED = "bom.created"
    BOM_LINE_ITEM_ADDED = "bom.line_item_added"
    BOM_LINE_ITEM_REMOVED = "bom.line_item_removed"
    BOM_CLONED = "bom.cloned"
    ECR_CREATED = "ecr.created"
    ECR_STATUS_CHANGED = "ecr.status_changed"
    ECO_CREATED = "eco.created"
    ECO_STATUS_CHANGED = "eco.status_changed"
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_REVISION_ADDED = "document.revision_added"
    COMPLIANCE_STATUS_CHANGED = "compliance.status_changed"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"
    COMPONENT_OBSOLESCENCE_ALERT = "component.obsolescence_alert"


class WebhookSubscription(Base):
    """A registered webhook endpoint that receives event notifications."""

    __tablename__ = "webhook_subscriptions"

    url: Mapped[str] = mapped_column(String(500))
    event: Mapped[WebhookEvent] = mapped_column(Enum(WebhookEvent), index=True)
    secret: Mapped[str] = mapped_column(String(200), default="")  # HMAC signing secret
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<Webhook {self.event.value} -> {self.url}>"
