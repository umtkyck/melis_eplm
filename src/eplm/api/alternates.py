"""Alternate component and Approved Vendor List API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.alternate import (
    AlternateComponentCreate,
    AlternateComponentResponse,
    AlternateComponentUpdate,
    ApprovedVendorCreate,
    ApprovedVendorResponse,
    ApprovedVendorUpdate,
)
from eplm.services.alternate_service import (
    AlternateNotFoundError,
    AlternateService,
    VendorNotFoundError,
)

router = APIRouter(prefix="/supply-chain", tags=["supply-chain"])


def _svc(db: AsyncSession = Depends(get_db)) -> AlternateService:
    return AlternateService(db)


# ── Alternates ───────────────────────────────────────────────────

@router.post(
    "/alternates", response_model=AlternateComponentResponse, status_code=201
)
async def add_alternate(
    data: AlternateComponentCreate, svc: AlternateService = Depends(_svc)
):
    return await svc.add_alternate(data)


@router.get(
    "/alternates/component/{component_id}",
    response_model=list[AlternateComponentResponse],
)
async def list_alternates(
    component_id: str, svc: AlternateService = Depends(_svc)
):
    return await svc.list_alternates(component_id)


@router.patch(
    "/alternates/{alternate_id}", response_model=AlternateComponentResponse
)
async def update_alternate(
    alternate_id: str,
    data: AlternateComponentUpdate,
    svc: AlternateService = Depends(_svc),
):
    try:
        return await svc.update_alternate(alternate_id, data)
    except AlternateNotFoundError as e:
        raise HTTPException(404, str(e))


# ── Approved Vendors ─────────────────────────────────────────────

@router.post("/vendors", response_model=ApprovedVendorResponse, status_code=201)
async def add_vendor(
    data: ApprovedVendorCreate, svc: AlternateService = Depends(_svc)
):
    return await svc.add_vendor(data)


@router.get(
    "/vendors/component/{component_id}",
    response_model=list[ApprovedVendorResponse],
)
async def list_vendors(
    component_id: str, svc: AlternateService = Depends(_svc)
):
    return await svc.list_vendors(component_id)


@router.patch("/vendors/{vendor_id}", response_model=ApprovedVendorResponse)
async def update_vendor(
    vendor_id: str,
    data: ApprovedVendorUpdate,
    svc: AlternateService = Depends(_svc),
):
    try:
        return await svc.update_vendor(vendor_id, data)
    except VendorNotFoundError as e:
        raise HTTPException(404, str(e))
