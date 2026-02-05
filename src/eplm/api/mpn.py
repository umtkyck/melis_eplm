"""Manufacturer Part Number cross-reference API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.mpn_xref import (
    ManufacturerPartCreate,
    ManufacturerPartResponse,
    ManufacturerPartUpdate,
)
from eplm.services.mpn_service import MpnNotFoundError, MpnService

router = APIRouter(prefix="/manufacturer-parts", tags=["manufacturer-parts"])


def _svc(db: AsyncSession = Depends(get_db)) -> MpnService:
    return MpnService(db)


@router.post("", response_model=ManufacturerPartResponse, status_code=201)
async def create_mpn(
    data: ManufacturerPartCreate, svc: MpnService = Depends(_svc)
):
    return await svc.create(data)


@router.get(
    "/component/{component_id}",
    response_model=list[ManufacturerPartResponse],
)
async def list_for_component(
    component_id: str, svc: MpnService = Depends(_svc)
):
    return await svc.list_for_component(component_id)


@router.get("/search", response_model=list[ManufacturerPartResponse])
async def search_by_mpn(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    svc: MpnService = Depends(_svc),
):
    return await svc.search_by_mpn(q, limit=limit)


@router.get("/at-risk", response_model=list[ManufacturerPartResponse])
async def get_at_risk(svc: MpnService = Depends(_svc)):
    return await svc.get_at_risk()


@router.get("/{mpn_id}", response_model=ManufacturerPartResponse)
async def get_mpn(mpn_id: str, svc: MpnService = Depends(_svc)):
    try:
        return await svc.get(mpn_id)
    except MpnNotFoundError as e:
        raise HTTPException(404, str(e))


@router.patch("/{mpn_id}", response_model=ManufacturerPartResponse)
async def update_mpn(
    mpn_id: str,
    data: ManufacturerPartUpdate,
    svc: MpnService = Depends(_svc),
):
    try:
        return await svc.update(mpn_id, data)
    except MpnNotFoundError as e:
        raise HTTPException(404, str(e))
