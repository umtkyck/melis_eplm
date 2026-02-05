"""Product management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.models.lifecycle import LifecyclePhase
from eplm.schemas.product import (
    PhaseTransitionRequest,
    ProductCreate,
    ProductResponse,
    ProductRevisionCreate,
    ProductRevisionResponse,
    ProductUpdate,
)
from eplm.services.product_service import (
    DuplicatePartNumberError,
    InvalidTransitionError,
    ProductNotFoundError,
    ProductService,
)

router = APIRouter(prefix="/products", tags=["products"])


def _svc(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(db)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(data: ProductCreate, svc: ProductService = Depends(_svc)):
    try:
        return await svc.create(data)
    except DuplicatePartNumberError as e:
        raise HTTPException(409, str(e))


@router.get("", response_model=list[ProductResponse])
async def list_products(
    phase: LifecyclePhase | None = None,
    category: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: ProductService = Depends(_svc),
):
    return await svc.list_all(phase=phase, category=category, offset=offset, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, svc: ProductService = Depends(_svc)):
    try:
        return await svc.get(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, data: ProductUpdate, svc: ProductService = Depends(_svc)
):
    try:
        return await svc.update(product_id, data)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/{product_id}/transition", response_model=ProductResponse)
async def transition_phase(
    product_id: str,
    request: PhaseTransitionRequest,
    svc: ProductService = Depends(_svc),
):
    try:
        return await svc.transition_phase(product_id, request)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))
    except InvalidTransitionError as e:
        raise HTTPException(400, str(e))


@router.post(
    "/{product_id}/revisions",
    response_model=ProductRevisionResponse,
    status_code=201,
)
async def create_revision(
    product_id: str,
    data: ProductRevisionCreate,
    svc: ProductService = Depends(_svc),
):
    try:
        return await svc.create_revision(product_id, data)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get(
    "/{product_id}/revisions", response_model=list[ProductRevisionResponse]
)
async def list_revisions(
    product_id: str, svc: ProductService = Depends(_svc)
):
    try:
        return await svc.get_revisions(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: str, svc: ProductService = Depends(_svc)):
    try:
        await svc.delete(product_id)
    except ProductNotFoundError as e:
        raise HTTPException(404, str(e))
