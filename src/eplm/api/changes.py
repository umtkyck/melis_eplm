"""Engineering change management API endpoints (ECR / ECO)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.models.change import ChangeOrderStatus, ChangeRequestStatus
from eplm.schemas.change import (
    ChangeOrderCreate,
    ChangeOrderItemCreate,
    ChangeOrderItemResponse,
    ChangeOrderResponse,
    ChangeOrderUpdate,
    ChangeRequestCreate,
    ChangeRequestResponse,
    ChangeRequestUpdate,
)
from eplm.services.change_service import (
    ChangeOrderNotFoundError,
    ChangeRequestNotFoundError,
    ChangeService,
    InvalidStatusError,
)

router = APIRouter(prefix="/changes", tags=["changes"])


def _svc(db: AsyncSession = Depends(get_db)) -> ChangeService:
    return ChangeService(db)


# ── ECR endpoints ───────────────────────────────────────────────

@router.post("/ecr", response_model=ChangeRequestResponse, status_code=201)
async def create_ecr(
    data: ChangeRequestCreate, svc: ChangeService = Depends(_svc)
):
    return await svc.create_ecr(data)


@router.get("/ecr", response_model=list[ChangeRequestResponse])
async def list_ecrs(
    status: ChangeRequestStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: ChangeService = Depends(_svc),
):
    return await svc.list_ecrs(status=status, offset=offset, limit=limit)


@router.get("/ecr/{ecr_id}", response_model=ChangeRequestResponse)
async def get_ecr(ecr_id: str, svc: ChangeService = Depends(_svc)):
    try:
        return await svc.get_ecr(ecr_id)
    except ChangeRequestNotFoundError as e:
        raise HTTPException(404, str(e))


@router.patch("/ecr/{ecr_id}", response_model=ChangeRequestResponse)
async def update_ecr(
    ecr_id: str,
    data: ChangeRequestUpdate,
    svc: ChangeService = Depends(_svc),
):
    try:
        return await svc.update_ecr(ecr_id, data)
    except ChangeRequestNotFoundError as e:
        raise HTTPException(404, str(e))
    except InvalidStatusError as e:
        raise HTTPException(400, str(e))


# ── ECO endpoints ───────────────────────────────────────────────

@router.post("/eco", response_model=ChangeOrderResponse, status_code=201)
async def create_eco(
    data: ChangeOrderCreate, svc: ChangeService = Depends(_svc)
):
    try:
        return await svc.create_eco(data)
    except ChangeRequestNotFoundError as e:
        raise HTTPException(404, str(e))
    except InvalidStatusError as e:
        raise HTTPException(400, str(e))


@router.get("/eco", response_model=list[ChangeOrderResponse])
async def list_ecos(
    status: ChangeOrderStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: ChangeService = Depends(_svc),
):
    return await svc.list_ecos(status=status, offset=offset, limit=limit)


@router.get("/eco/{eco_id}", response_model=ChangeOrderResponse)
async def get_eco(eco_id: str, svc: ChangeService = Depends(_svc)):
    try:
        return await svc.get_eco(eco_id)
    except ChangeOrderNotFoundError as e:
        raise HTTPException(404, str(e))


@router.patch("/eco/{eco_id}", response_model=ChangeOrderResponse)
async def update_eco(
    eco_id: str,
    data: ChangeOrderUpdate,
    svc: ChangeService = Depends(_svc),
):
    try:
        return await svc.update_eco(eco_id, data)
    except ChangeOrderNotFoundError as e:
        raise HTTPException(404, str(e))
    except InvalidStatusError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/eco/{eco_id}/items",
    response_model=ChangeOrderItemResponse,
    status_code=201,
)
async def add_eco_item(
    eco_id: str,
    data: ChangeOrderItemCreate,
    svc: ChangeService = Depends(_svc),
):
    try:
        return await svc.add_eco_item(eco_id, data)
    except ChangeOrderNotFoundError as e:
        raise HTTPException(404, str(e))
