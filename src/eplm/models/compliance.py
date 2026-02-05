"""Regulatory compliance and standards tracking for electronics products."""

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class ComplianceStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"
    EXEMPT = "exempt"


class ComplianceStandard(Base):
    """A regulatory standard or certification (e.g. CE, FCC, UL, RoHS, REACH)."""

    __tablename__ = "compliance_standards"

    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    issuing_body: Mapped[str] = mapped_column(String(200), default="")
    region: Mapped[str] = mapped_column(String(100), default="")  # e.g. "EU", "US", "Global"

    records: Mapped[list["ComplianceRecord"]] = relationship(
        back_populates="standard"
    )

    def __repr__(self) -> str:
        return f"<ComplianceStandard {self.code}>"


class ComplianceRecord(Base):
    """Tracks a product's compliance status against a specific standard."""

    __tablename__ = "compliance_records"

    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    standard_id: Mapped[str] = mapped_column(
        ForeignKey("compliance_standards.id"), index=True
    )
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus), default=ComplianceStatus.NOT_STARTED
    )
    certificate_number: Mapped[str] = mapped_column(String(100), default="")
    test_lab: Mapped[str] = mapped_column(String(200), default="")
    tested_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    product: Mapped["Product"] = relationship(back_populates="compliance_records")  # noqa: F821
    standard: Mapped["ComplianceStandard"] = relationship(back_populates="records")

    @property
    def is_valid(self) -> bool:
        """Return True if the certification is currently valid."""
        if self.status != ComplianceStatus.PASSED:
            return False
        if self.expiry_date and self.expiry_date < date.today():
            return False
        return True

    def __repr__(self) -> str:
        return f"<ComplianceRecord product={self.product_id} std={self.standard_id} [{self.status.value}]>"
