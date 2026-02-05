"""Component management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.models.component import ComponentCategoryEnum
from eplm.models.lifecycle import LifecyclePhase
from eplm.schemas.component import ComponentCreate, ComponentResponse, ComponentUpdate
from eplm.services.component_service import (
    ComponentNotFoundError,
    ComponentService,
    DuplicateComponentError,
)

router = APIRouter(prefix="/components", tags=["components"])


def _svc(db: AsyncSession = Depends(get_db)) -> ComponentService:
    return ComponentService(db)


@router.post("", response_model=ComponentResponse, status_code=201)
async def create_component(
    data: ComponentCreate, svc: ComponentService = Depends(_svc)
):
    try:
        return await svc.create(data)
    except DuplicateComponentError as e:
        raise HTTPException(409, str(e))


@router.get("", response_model=list[ComponentResponse])
async def list_components(
    category: ComponentCategoryEnum | None = None,
    phase: LifecyclePhase | None = None,
    manufacturer: str | None = None,
    rohs_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    svc: ComponentService = Depends(_svc),
):
    return await svc.list_all(
        category=category,
        phase=phase,
        manufacturer=manufacturer,
        rohs_only=rohs_only,
        offset=offset,
        limit=limit,
    )


@router.get("/search", response_model=list[ComponentResponse])
async def search_components(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    svc: ComponentService = Depends(_svc),
):
    return await svc.search(q, limit=limit)


@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component(
    component_id: str, svc: ComponentService = Depends(_svc)
):
    try:
        return await svc.get(component_id)
    except ComponentNotFoundError as e:
        raise HTTPException(404, str(e))


@router.patch("/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: str,
    data: ComponentUpdate,
    svc: ComponentService = Depends(_svc),
):
    try:
        return await svc.update(component_id, data)
    except ComponentNotFoundError as e:
        raise HTTPException(404, str(e))


@router.delete("/{component_id}", status_code=204)
async def delete_component(
    component_id: str, svc: ComponentService = Depends(_svc)
):
    try:
        await svc.delete(component_id)
    except ComponentNotFoundError as e:
        raise HTTPException(404, str(e))
