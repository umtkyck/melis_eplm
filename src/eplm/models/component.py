"""Electronic component and component revision models."""

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eplm.models.base import Base
from eplm.models.lifecycle import LifecyclePhase


class ComponentCategory(str, Enum):
    """High-level classification for electronic components."""

    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    IC = "integrated_circuit"
    CONNECTOR = "connector"
    PCB = "pcb"
    MECHANICAL = "mechanical"
    SENSOR = "sensor"
    POWER = "power"
    CRYSTAL = "crystal"
    LED = "led"
    RELAY = "relay"
    FUSE = "fuse"
    OTHER = "other"


import enum as _enum


class ComponentCategoryEnum(str, _enum.Enum):
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    TRANSISTOR = "transistor"
    IC = "integrated_circuit"
    CONNECTOR = "connector"
    PCB = "pcb"
    MECHANICAL = "mechanical"
    SENSOR = "sensor"
    POWER = "power"
    CRYSTAL = "crystal"
    LED = "led"
    RELAY = "relay"
    FUSE = "fuse"
    OTHER = "other"


class Component(Base):
    """An individual electronic component (resistor, IC, connector, etc.).

    Components are referenced by BOM line items and carry their own lifecycle phase,
    supplier info, and package/footprint data relevant to electronics design.
    """

    __tablename__ = "components"

    part_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    manufacturer_pn: Mapped[str] = mapped_column(String(100), default="")
    manufacturer: Mapped[str] = mapped_column(String(200), default="")
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[ComponentCategoryEnum] = mapped_column(
        Enum(ComponentCategoryEnum), default=ComponentCategoryEnum.OTHER
    )
    package: Mapped[str] = mapped_column(String(50), default="")  # e.g. "0402", "QFN-48"
    value: Mapped[str] = mapped_column(String(50), default="")  # e.g. "10kΩ", "100nF"
    datasheet_url: Mapped[str] = mapped_column(String(500), default="")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_days: Mapped[int] = mapped_column(default=0)
    phase: Mapped[LifecyclePhase] = mapped_column(
        Enum(LifecyclePhase), default=LifecyclePhase.ACTIVE
    )
    rohs_compliant: Mapped[bool] = mapped_column(default=False)

    revisions: Mapped[list["ComponentRevision"]] = relationship(
        back_populates="component", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Component {self.part_number} '{self.name}'>"


class ComponentRevision(Base):
    """Tracks revision history for a component."""

    __tablename__ = "component_revisions"

    component_id: Mapped[str] = mapped_column(ForeignKey("components.id"), index=True)
    revision: Mapped[str] = mapped_column(String(10))
    change_summary: Mapped[str] = mapped_column(Text, default="")

    component: Mapped["Component"] = relationship(back_populates="revisions")

    def __repr__(self) -> str:
        return f"<ComponentRevision {self.component_id} rev={self.revision}>"
