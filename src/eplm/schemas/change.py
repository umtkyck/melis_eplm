"""Pydantic schemas for engineering change management."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.change import (
    ChangeImpact,
    ChangeOrderStatus,
    ChangeRequestStatus,
)


class ChangeRequestCreate(BaseModel):
    ecr_number: str = Field(..., min_length=1, max_length=30)
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    reason: str = ""
    impact: ChangeImpact = ChangeImpact.MEDIUM
    requested_by: str = ""
    product_id: str | None = None


class ChangeRequestUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    reason: str | None = None
    impact: ChangeImpact | None = None
    status: ChangeRequestStatus | None = None
    reviewed_by: str | None = None


class ChangeRequestResponse(BaseModel):
    id: str
    ecr_number: str
    title: str
    description: str
    reason: str
    impact: ChangeImpact
    status: ChangeRequestStatus
    requested_by: str
    reviewed_by: str
    product_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChangeOrderCreate(BaseModel):
    eco_number: str = Field(..., min_length=1, max_length=30)
    change_request_id: str
    title: str = Field(..., min_length=1, max_length=300)
    description: str = ""
    assigned_to: str = ""


class ChangeOrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ChangeOrderStatus | None = None
    assigned_to: str | None = None
    approved_by: str | None = None


class ChangeOrderResponse(BaseModel):
    id: str
    eco_number: str
    change_request_id: str
    title: str
    description: str
    status: ChangeOrderStatus
    assigned_to: str
    approved_by: str
    approved_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChangeOrderItemCreate(BaseModel):
    item_type: str = Field(..., pattern="^(product|component)$")
    item_id: str
    from_revision: str = ""
    to_revision: str = ""
    change_description: str = ""


class ChangeOrderItemResponse(BaseModel):
    id: str
    change_order_id: str
    item_type: str
    item_id: str
    from_revision: str
    to_revision: str
    change_description: str
    created_at: datetime

    model_config = {"from_attributes": True}
