"""Pydantic schemas for BOM management."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.lifecycle import LifecyclePhase


class BomCreate(BaseModel):
    product_id: str
    revision: str = "1"
    name: str = ""
    description: str = ""


class BomResponse(BaseModel):
    id: str
    product_id: str
    revision: str
    name: str
    description: str
    phase: LifecyclePhase
    is_active: bool
    total_cost: float
    component_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BomLineItemCreate(BaseModel):
    component_id: str
    reference: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(default=1, ge=1)
    unit_cost: float = Field(default=0.0, ge=0)
    notes: str = ""
    do_not_populate: bool = False


class BomLineItemResponse(BaseModel):
    id: str
    bom_id: str
    component_id: str
    reference: str
    quantity: int
    unit_cost: float
    notes: str
    do_not_populate: bool
    line_cost: float
    created_at: datetime

    model_config = {"from_attributes": True}
