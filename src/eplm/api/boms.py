"""Bill of Materials API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.bom import BomCreate, BomLineItemCreate, BomLineItemResponse, BomResponse
from eplm.services.bom_service import BomNotFoundError, BomService, LineItemConflictError

router = APIRouter(prefix="/boms", tags=["boms"])


def _svc(db: AsyncSession = Depends(get_db)) -> BomService:
    return BomService(db)


@router.post("", response_model=BomResponse, status_code=201)
async def create_bom(data: BomCreate, svc: BomService = Depends(_svc)):
    return await svc.create(data)


@router.get("/product/{product_id}", response_model=list[BomResponse])
async def list_boms_for_product(
    product_id: str, svc: BomService = Depends(_svc)
):
    return await svc.list_for_product(product_id)


@router.get("/{bom_id}", response_model=BomResponse)
async def get_bom(bom_id: str, svc: BomService = Depends(_svc)):
    try:
        return await svc.get(bom_id)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post(
    "/{bom_id}/items", response_model=BomLineItemResponse, status_code=201
)
async def add_line_item(
    bom_id: str,
    data: BomLineItemCreate,
    svc: BomService = Depends(_svc),
):
    try:
        return await svc.add_line_item(bom_id, data)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))
    except LineItemConflictError as e:
        raise HTTPException(409, str(e))


@router.delete("/items/{line_item_id}", status_code=204)
async def remove_line_item(
    line_item_id: str, svc: BomService = Depends(_svc)
):
    try:
        await svc.remove_line_item(line_item_id)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/{bom_id}/cost-summary")
async def cost_summary(bom_id: str, svc: BomService = Depends(_svc)):
    try:
        return await svc.get_cost_summary(bom_id)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/{bom_id}/clone", response_model=BomResponse, status_code=201)
async def clone_bom(
    bom_id: str, new_revision: str, svc: BomService = Depends(_svc)
):
    try:
        return await svc.clone_bom(bom_id, new_revision)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/{bom_id}", status_code=204)
async def delete_bom(bom_id: str, svc: BomService = Depends(_svc)):
    try:
        await svc.delete(bom_id)
    except BomNotFoundError as e:
        raise HTTPException(404, str(e))
