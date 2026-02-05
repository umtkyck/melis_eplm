"""Product and product revision models."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base
from eplm.models.lifecycle import LifecyclePhase


class Product(Base):
    """Top-level electronics product (e.g. a circuit board, sensor module, device).

    A product aggregates components via a BOM and moves through lifecycle phases
    from concept to end-of-life.
    """

    __tablename__ = "products"

    part_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    phase: Mapped[LifecyclePhase] = mapped_column(
        Enum(LifecyclePhase), default=LifecyclePhase.CONCEPT
    )
    owner: Mapped[str] = mapped_column(String(200), default="")

    revisions: Mapped[list["ProductRevision"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductRevision.revision"
    )
    boms: Mapped[list["BillOfMaterials"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
    compliance_records: Mapped[list["ComplianceRecord"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Product {self.part_number} [{self.phase.value}]>"


class ProductRevision(Base):
    """Immutable snapshot of a product at a specific revision level."""

    __tablename__ = "product_revisions"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    revision: Mapped[str] = mapped_column(String(10))  # e.g. "A", "B", "1.0"
    change_summary: Mapped[str] = mapped_column(Text, default="")
    phase_at_creation: Mapped[LifecyclePhase] = mapped_column(
        Enum(LifecyclePhase), default=LifecyclePhase.CONCEPT
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by: Mapped[str] = mapped_column(String(200), default="")

    product: Mapped["Product"] = relationship(back_populates="revisions")

    def __repr__(self) -> str:
        return f"<ProductRevision {self.product_id} rev={self.revision}>"
