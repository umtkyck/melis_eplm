"""Bill of Materials models for electronics product management."""

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base
from eplm.models.lifecycle import LifecyclePhase


class BillOfMaterials(Base):
    """A versioned bill of materials tied to a product.

    Each product can have multiple BOM versions (e.g. for different revisions
    or manufacturing variants).
    """

    __tablename__ = "boms"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    revision: Mapped[str] = mapped_column(String(10), default="1")
    name: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    phase: Mapped[LifecyclePhase] = mapped_column(
        Enum(LifecyclePhase), default=LifecyclePhase.DESIGN
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    product: Mapped["Product"] = relationship(back_populates="boms")  # noqa: F821
    line_items: Mapped[list["BomLineItem"]] = relationship(
        back_populates="bom", cascade="all, delete-orphan", order_by="BomLineItem.reference"
    )

    @property
    def total_cost(self) -> float:
        """Sum of (quantity * unit_cost) for every line item."""
        return sum(item.quantity * item.unit_cost for item in self.line_items)

    @property
    def component_count(self) -> int:
        return len(self.line_items)

    def __repr__(self) -> str:
        return f"<BOM product={self.product_id} rev={self.revision}>"


class BomLineItem(Base):
    """A single row in a BOM — maps a component to a quantity and reference designator."""

    __tablename__ = "bom_line_items"
    __table_args__ = (
        UniqueConstraint("bom_id", "reference", name="uq_bom_reference"),
    )

    bom_id: Mapped[str] = mapped_column(ForeignKey("boms.id"), index=True)
    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    reference: Mapped[str] = mapped_column(String(50))  # e.g. "R1", "U3", "C12"
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str] = mapped_column(Text, default="")
    do_not_populate: Mapped[bool] = mapped_column(default=False)

    bom: Mapped["BillOfMaterials"] = relationship(back_populates="line_items")
    component: Mapped["Component"] = relationship()  # noqa: F821

    @property
    def line_cost(self) -> float:
        return self.quantity * self.unit_cost

    def __repr__(self) -> str:
        return f"<BomLineItem {self.reference} qty={self.quantity}>"
