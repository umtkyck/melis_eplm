"""Manufacturer part number cross-reference and lifecycle tracking.

Electronics-specific: track multiple manufacturer sources per internal part,
detect obsolescence risks, and find cross-references across manufacturers.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.models.mpn_xref import ManufacturerPart, ManufacturerStatus
from eplm.schemas.mpn_xref import ManufacturerPartCreate, ManufacturerPartUpdate


class MpnServiceError(Exception):
    pass


class MpnNotFoundError(MpnServiceError):
    pass


class MpnService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ManufacturerPartCreate) -> ManufacturerPart:
        mpn = ManufacturerPart(**data.model_dump())
        self.db.add(mpn)
        await self.db.commit()
        await self.db.refresh(mpn)
        return mpn

    async def get(self, mpn_id: str) -> ManufacturerPart:
        result = await self.db.execute(
            select(ManufacturerPart).where(ManufacturerPart.id == mpn_id)
        )
        mpn = result.scalar_one_or_none()
        if not mpn:
            raise MpnNotFoundError(f"Manufacturer part '{mpn_id}' not found")
        return mpn

    async def list_for_component(self, component_id: str) -> list[ManufacturerPart]:
        result = await self.db.execute(
            select(ManufacturerPart)
            .where(ManufacturerPart.component_id == component_id)
            .order_by(ManufacturerPart.manufacturer)
        )
        return list(result.scalars().all())

    async def search_by_mpn(self, mpn_query: str, limit: int = 20) -> list[ManufacturerPart]:
        """Cross-reference search: find components by manufacturer part number."""
        pattern = f"%{mpn_query}%"
        result = await self.db.execute(
            select(ManufacturerPart)
            .where(ManufacturerPart.mpn.ilike(pattern))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_at_risk(self) -> list[ManufacturerPart]:
        """Return all manufacturer parts flagged as NRND, LTB, EOL, or obsolete."""
        result = await self.db.execute(
            select(ManufacturerPart)
            .where(
                ManufacturerPart.status.in_([
                    ManufacturerStatus.NRND,
                    ManufacturerStatus.LAST_TIME_BUY,
                    ManufacturerStatus.EOL,
                    ManufacturerStatus.OBSOLETE,
                ])
            )
            .order_by(ManufacturerPart.status, ManufacturerPart.manufacturer)
        )
        return list(result.scalars().all())

    async def update(self, mpn_id: str, data: ManufacturerPartUpdate) -> ManufacturerPart:
        mpn = await self.get(mpn_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(mpn, field, value)
        await self.db.commit()
        await self.db.refresh(mpn)
        return mpn
