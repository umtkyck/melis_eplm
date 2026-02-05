"""Component CRUD operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.models.component import Component, ComponentCategoryEnum, ComponentRevision
from eplm.models.lifecycle import LifecyclePhase
from eplm.schemas.component import ComponentCreate, ComponentUpdate


class ComponentServiceError(Exception):
    pass


class ComponentNotFoundError(ComponentServiceError):
    pass


class DuplicateComponentError(ComponentServiceError):
    pass


class ComponentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ComponentCreate) -> Component:
        existing = await self.db.execute(
            select(Component).where(Component.part_number == data.part_number)
        )
        if existing.scalar_one_or_none():
            raise DuplicateComponentError(
                f"Component part number '{data.part_number}' already exists"
            )
        component = Component(**data.model_dump())
        self.db.add(component)
        await self.db.commit()
        await self.db.refresh(component)
        return component

    async def get(self, component_id: str) -> Component:
        result = await self.db.execute(
            select(Component).where(Component.id == component_id)
        )
        component = result.scalar_one_or_none()
        if not component:
            raise ComponentNotFoundError(f"Component '{component_id}' not found")
        return component

    async def list_all(
        self,
        category: ComponentCategoryEnum | None = None,
        phase: LifecyclePhase | None = None,
        manufacturer: str | None = None,
        rohs_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Component]:
        query = select(Component)
        if category:
            query = query.where(Component.category == category)
        if phase:
            query = query.where(Component.phase == phase)
        if manufacturer:
            query = query.where(Component.manufacturer == manufacturer)
        if rohs_only:
            query = query.where(Component.rohs_compliant.is_(True))
        query = query.offset(offset).limit(limit).order_by(Component.part_number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, component_id: str, data: ComponentUpdate) -> Component:
        component = await self.get(component_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)
        await self.db.commit()
        await self.db.refresh(component)
        return component

    async def search(self, query_str: str, limit: int = 20) -> list[Component]:
        """Search components by part number, name, or manufacturer part number."""
        pattern = f"%{query_str}%"
        query = (
            select(Component)
            .where(
                Component.part_number.ilike(pattern)
                | Component.name.ilike(pattern)
                | Component.manufacturer_pn.ilike(pattern)
            )
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete(self, component_id: str) -> None:
        component = await self.get(component_id)
        await self.db.delete(component)
        await self.db.commit()
