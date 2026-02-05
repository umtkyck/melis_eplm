"""Pydantic schemas for components."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.component import ComponentCategoryEnum
from eplm.models.lifecycle import LifecyclePhase


class ComponentCreate(BaseModel):
    part_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    manufacturer_pn: str = ""
    manufacturer: str = ""
    description: str = ""
    category: ComponentCategoryEnum = ComponentCategoryEnum.OTHER
    package: str = ""
    value: str = ""
    datasheet_url: str = ""
    unit_cost: float = 0.0
    lead_time_days: int = 0
    rohs_compliant: bool = False


class ComponentUpdate(BaseModel):
    name: str | None = None
    manufacturer_pn: str | None = None
    manufacturer: str | None = None
    description: str | None = None
    category: ComponentCategoryEnum | None = None
    package: str | None = None
    value: str | None = None
    datasheet_url: str | None = None
    unit_cost: float | None = None
    lead_time_days: int | None = None
    rohs_compliant: bool | None = None


class ComponentResponse(BaseModel):
    id: str
    part_number: str
    manufacturer_pn: str
    manufacturer: str
    name: str
    description: str
    category: ComponentCategoryEnum
    package: str
    value: str
    datasheet_url: str
    unit_cost: float
    lead_time_days: int
    phase: LifecyclePhase
    rohs_compliant: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
