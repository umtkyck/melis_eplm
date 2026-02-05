"""Compliance and regulatory tracking API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.compliance import (
    ComplianceRecordCreate,
    ComplianceRecordResponse,
    ComplianceRecordUpdate,
    ComplianceStandardCreate,
    ComplianceStandardResponse,
)
from eplm.services.compliance_service import (
    ComplianceService,
    RecordNotFoundError,
    StandardNotFoundError,
)

router = APIRouter(prefix="/compliance", tags=["compliance"])


def _svc(db: AsyncSession = Depends(get_db)) -> ComplianceService:
    return ComplianceService(db)


# ── Standards ───────────────────────────────────────────────────

@router.post(
    "/standards", response_model=ComplianceStandardResponse, status_code=201
)
async def create_standard(
    data: ComplianceStandardCreate, svc: ComplianceService = Depends(_svc)
):
    return await svc.create_standard(data)


@router.get("/standards", response_model=list[ComplianceStandardResponse])
async def list_standards(svc: ComplianceService = Depends(_svc)):
    return await svc.list_standards()


@router.get(
    "/standards/{standard_id}", response_model=ComplianceStandardResponse
)
async def get_standard(
    standard_id: str, svc: ComplianceService = Depends(_svc)
):
    try:
        return await svc.get_standard(standard_id)
    except StandardNotFoundError as e:
        raise HTTPException(404, str(e))


# ── Records ─────────────────────────────────────────────────────

@router.post("/records", response_model=ComplianceRecordResponse, status_code=201)
async def create_record(
    data: ComplianceRecordCreate, svc: ComplianceService = Depends(_svc)
):
    return await svc.create_record(data)


@router.get(
    "/records/product/{product_id}",
    response_model=list[ComplianceRecordResponse],
)
async def list_records_for_product(
    product_id: str, svc: ComplianceService = Depends(_svc)
):
    return await svc.list_records_for_product(product_id)


@router.patch(
    "/records/{record_id}", response_model=ComplianceRecordResponse
)
async def update_record(
    record_id: str,
    data: ComplianceRecordUpdate,
    svc: ComplianceService = Depends(_svc),
):
    try:
        return await svc.update_record(record_id, data)
    except RecordNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/summary/{product_id}")
async def compliance_summary(
    product_id: str, svc: ComplianceService = Depends(_svc)
):
    return await svc.get_compliance_summary(product_id)
