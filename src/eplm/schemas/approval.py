"""Pydantic schemas for approval workflow engine."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.approval import ApprovalStatus


class ApprovalTemplateStepCreate(BaseModel):
    step_order: int = Field(..., ge=1)
    role: str = Field(..., min_length=1, max_length=100)
    approver: str = ""
    is_required: bool = True
    auto_approve_after_hours: int = Field(default=0, ge=0)


class ApprovalTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    entity_type: str = Field(..., min_length=1, max_length=50)
    description: str = ""
    steps: list[ApprovalTemplateStepCreate] = []


class ApprovalTemplateStepResponse(BaseModel):
    id: str
    step_order: int
    role: str
    approver: str
    is_required: bool
    auto_approve_after_hours: int

    model_config = {"from_attributes": True}


class ApprovalTemplateResponse(BaseModel):
    id: str
    name: str
    entity_type: str
    description: str
    is_active: bool
    steps: list[ApprovalTemplateStepResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequestCreate(BaseModel):
    entity_type: str
    entity_id: str
    template_id: str | None = None
    title: str = Field(..., min_length=1, max_length=300)


class ApprovalDecisionCreate(BaseModel):
    decided_by: str = Field(..., min_length=1)
    status: ApprovalStatus
    comment: str = ""


class ApprovalDecisionResponse(BaseModel):
    id: str
    request_id: str
    step_order: int
    role: str
    decided_by: str
    status: ApprovalStatus
    comment: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequestResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    template_id: str | None
    title: str
    current_step: int
    is_complete: bool
    is_approved: bool
    decisions: list[ApprovalDecisionResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
