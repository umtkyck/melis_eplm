"""Pydantic schemas for manufacturer part cross-reference."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from eplm.models.mpn_xref import ManufacturerStatus


class ManufacturerPartCreate(BaseModel):
    component_id: str
    manufacturer: str = Field(..., min_length=1, max_length=200)
    mpn: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    status: ManufacturerStatus = ManufacturerStatus.ACTIVE
    datasheet_url: str = ""
    eol_date: date | None = None
    last_buy_date: date | None = None
    replacement_mpn: str = ""
    notes: str = ""


class ManufacturerPartUpdate(BaseModel):
    status: ManufacturerStatus | None = None
    datasheet_url: str | None = None
    eol_date: date | None = None
    last_buy_date: date | None = None
    replacement_mpn: str | None = None
    notes: str | None = None


class ManufacturerPartResponse(BaseModel):
    id: str
    component_id: str
    manufacturer: str
    mpn: str
    description: str
    status: ManufacturerStatus
    datasheet_url: str
    eol_date: date | None
    last_buy_date: date | None
    replacement_mpn: str
    notes: str
    is_at_risk: bool
    created_at: datetime

    model_config = {"from_attributes": True}
