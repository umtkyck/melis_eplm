"""Manufacturer Part Number cross-reference and lifecycle tracking.

Electronics-specific: components are sourced from multiple manufacturers with
different part numbers. Engineers need to track MPN equivalencies and
manufacturer lifecycle status to anticipate obsolescence.

Addresses IFS complaint: CAD/PLM-to-ERP integration is fragile when
engineering and manufacturing use different part numbering.
"""

import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base


class ManufacturerStatus(str, enum.Enum):
    ACTIVE = "active"
    NRND = "nrnd"  # Not Recommended for New Designs
    LAST_TIME_BUY = "last_time_buy"
    EOL = "eol"  # End of Life
    OBSOLETE = "obsolete"


class ManufacturerPart(Base):
    """A manufacturer's part that maps to an internal component.

    Supports tracking multiple manufacturer sources per internal part number,
    including lifecycle status from the manufacturer's perspective.
    """

    __tablename__ = "manufacturer_parts"

    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    manufacturer: Mapped[str] = mapped_column(String(200), index=True)
    mpn: Mapped[str] = mapped_column(String(100), index=True)  # manufacturer part number
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ManufacturerStatus] = mapped_column(
        Enum(ManufacturerStatus), default=ManufacturerStatus.ACTIVE
    )
    datasheet_url: Mapped[str] = mapped_column(String(500), default="")
    eol_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_buy_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    replacement_mpn: Mapped[str] = mapped_column(String(100), default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    component: Mapped["Component"] = relationship()  # noqa: F821

    @property
    def is_at_risk(self) -> bool:
        """True if the manufacturer has signaled end-of-life or last-time-buy."""
        return self.status in (
            ManufacturerStatus.NRND,
            ManufacturerStatus.LAST_TIME_BUY,
            ManufacturerStatus.EOL,
            ManufacturerStatus.OBSOLETE,
        )

    def __repr__(self) -> str:
        return f"<ManufacturerPart {self.manufacturer} {self.mpn} [{self.status.value}]>"
