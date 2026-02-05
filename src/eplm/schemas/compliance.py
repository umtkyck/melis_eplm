"""Pydantic schemas for compliance tracking."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from eplm.models.compliance import ComplianceStatus


class ComplianceStandardCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    issuing_body: str = ""
    region: str = ""


class ComplianceStandardResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str
    issuing_body: str
    region: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplianceRecordCreate(BaseModel):
    product_id: str
    standard_id: str
    status: ComplianceStatus = ComplianceStatus.NOT_STARTED
    certificate_number: str = ""
    test_lab: str = ""
    tested_date: date | None = None
    expiry_date: date | None = None
    notes: str = ""


class ComplianceRecordUpdate(BaseModel):
    status: ComplianceStatus | None = None
    certificate_number: str | None = None
    test_lab: str | None = None
    tested_date: date | None = None
    expiry_date: date | None = None
    notes: str | None = None


class ComplianceRecordResponse(BaseModel):
    id: str
    product_id: str
    standard_id: str
    status: ComplianceStatus
    certificate_number: str
    test_lab: str
    tested_date: date | None
    expiry_date: date | None
    notes: str
    is_valid: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
