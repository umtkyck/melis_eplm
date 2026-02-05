"""Alternate/substitute components and Approved Vendor List (AVL).

Electronics-specific: supply chain resilience is critical. Engineers need to
track approved alternates for every component so manufacturing can substitute
when a part is unavailable or obsolete.

Also addresses IFS complaint about eBOM-to-mBOM friction — alternates bridge
engineering specifications to manufacturing realities.
"""

import enum

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class AlternateStatus(str, enum.Enum):
    PROPOSED = "proposed"
    TESTING = "testing"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class AlternateComponent(Base):
    """An approved alternate/substitute for a primary component.

    Tracks form/fit/function compatibility and approval status.
    """

    __tablename__ = "alternate_components"
    __table_args__ = (
        UniqueConstraint("primary_component_id", "alternate_component_id", name="uq_alternate_pair"),
    )

    primary_component_id: Mapped[str] = mapped_column(
        ForeignKey("components.id"), index=True
    )
    alternate_component_id: Mapped[str] = mapped_column(
        ForeignKey("components.id"), index=True
    )
    status: Mapped[AlternateStatus] = mapped_column(
        Enum(AlternateStatus), default=AlternateStatus.PROPOSED
    )
    priority: Mapped[int] = mapped_column(Integer, default=1)  # 1 = preferred alternate
    form_fit_function: Mapped[bool] = mapped_column(default=False)  # true = drop-in replacement
    notes: Mapped[str] = mapped_column(Text, default="")
    approved_by: Mapped[str] = mapped_column(String(200), default="")

    primary_component: Mapped["Component"] = relationship(  # noqa: F821
        foreign_keys=[primary_component_id]
    )
    alternate_component: Mapped["Component"] = relationship(  # noqa: F821
        foreign_keys=[alternate_component_id]
    )

    def __repr__(self) -> str:
        return f"<Alternate {self.primary_component_id} -> {self.alternate_component_id}>"


class VendorStatus(str, enum.Enum):
    ACTIVE = "active"
    PREFERRED = "preferred"
    APPROVED = "approved"
    UNDER_REVIEW = "under_review"
    DISQUALIFIED = "disqualified"


class ApprovedVendor(Base):
    """Approved Vendor List entry — tracks vendors qualified to supply a component.

    Electronics manufacturing requires vendor qualification to ensure quality,
    delivery reliability, and counterfeit prevention.
    """

    __tablename__ = "approved_vendors"
    __table_args__ = (
        UniqueConstraint("component_id", "vendor_name", name="uq_component_vendor"),
    )

    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    vendor_name: Mapped[str] = mapped_column(String(200))
    vendor_pn: Mapped[str] = mapped_column(String(100), default="")  # vendor's part number
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus), default=VendorStatus.UNDER_REVIEW
    )
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    min_order_qty: Mapped[int] = mapped_column(Integer, default=1)
    country_of_origin: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    component: Mapped["Component"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ApprovedVendor {self.vendor_name} for {self.component_id}>"
