"""Pydantic schemas for alternate components and AVL."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.alternate import AlternateStatus, VendorStatus


class AlternateComponentCreate(BaseModel):
    primary_component_id: str
    alternate_component_id: str
    priority: int = Field(default=1, ge=1)
    form_fit_function: bool = False
    notes: str = ""


class AlternateComponentUpdate(BaseModel):
    status: AlternateStatus | None = None
    priority: int | None = None
    form_fit_function: bool | None = None
    notes: str | None = None
    approved_by: str | None = None


class AlternateComponentResponse(BaseModel):
    id: str
    primary_component_id: str
    alternate_component_id: str
    status: AlternateStatus
    priority: int
    form_fit_function: bool
    notes: str
    approved_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovedVendorCreate(BaseModel):
    component_id: str
    vendor_name: str = Field(..., min_length=1, max_length=200)
    vendor_pn: str = ""
    unit_cost: float = Field(default=0.0, ge=0)
    lead_time_days: int = Field(default=0, ge=0)
    min_order_qty: int = Field(default=1, ge=1)
    country_of_origin: str = ""
    notes: str = ""


class ApprovedVendorUpdate(BaseModel):
    status: VendorStatus | None = None
    vendor_pn: str | None = None
    unit_cost: float | None = None
    lead_time_days: int | None = None
    min_order_qty: int | None = None
    country_of_origin: str | None = None
    notes: str | None = None


class ApprovedVendorResponse(BaseModel):
    id: str
    component_id: str
    vendor_name: str
    vendor_pn: str
    status: VendorStatus
    unit_cost: float
    lead_time_days: int
    min_order_qty: int
    country_of_origin: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}
