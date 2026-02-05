"""Pydantic schemas for products."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.lifecycle import LifecyclePhase


class ProductCreate(BaseModel):
    part_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    category: str = ""
    owner: str = ""


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    owner: str | None = None


class ProductResponse(BaseModel):
    id: str
    part_number: str
    name: str
    description: str
    category: str
    phase: LifecyclePhase
    owner: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PhaseTransitionRequest(BaseModel):
    target_phase: LifecyclePhase
    reason: str = ""


class ProductRevisionCreate(BaseModel):
    revision: str = Field(..., min_length=1, max_length=10)
    change_summary: str = ""


class ProductRevisionResponse(BaseModel):
    id: str
    product_id: str
    revision: str
    change_summary: str
    phase_at_creation: LifecyclePhase
    released_at: datetime | None
    released_by: str
    created_at: datetime

    model_config = {"from_attributes": True}
