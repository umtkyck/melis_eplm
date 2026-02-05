"""Alternate component and Approved Vendor List management.

Electronics-specific: supply chain resilience requires tracking approved
substitutes and multiple qualified vendors per component.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.models.alternate import AlternateComponent, AlternateStatus, ApprovedVendor
from eplm.schemas.alternate import (
    AlternateComponentCreate,
    AlternateComponentUpdate,
    ApprovedVendorCreate,
    ApprovedVendorUpdate,
)


class AlternateServiceError(Exception):
    pass


class AlternateNotFoundError(AlternateServiceError):
    pass


class VendorNotFoundError(AlternateServiceError):
    pass


class AlternateService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Alternate components ──────────────────────────────────────

    async def add_alternate(self, data: AlternateComponentCreate) -> AlternateComponent:
        alt = AlternateComponent(**data.model_dump())
        self.db.add(alt)
        await self.db.commit()
        await self.db.refresh(alt)
        return alt

    async def list_alternates(self, component_id: str) -> list[AlternateComponent]:
        result = await self.db.execute(
            select(AlternateComponent)
            .where(AlternateComponent.primary_component_id == component_id)
            .order_by(AlternateComponent.priority)
        )
        return list(result.scalars().all())

    async def update_alternate(
        self, alternate_id: str, data: AlternateComponentUpdate
    ) -> AlternateComponent:
        result = await self.db.execute(
            select(AlternateComponent).where(AlternateComponent.id == alternate_id)
        )
        alt = result.scalar_one_or_none()
        if not alt:
            raise AlternateNotFoundError(f"Alternate '{alternate_id}' not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(alt, field, value)
        await self.db.commit()
        await self.db.refresh(alt)
        return alt

    # ── Approved Vendor List ──────────────────────────────────────

    async def add_vendor(self, data: ApprovedVendorCreate) -> ApprovedVendor:
        vendor = ApprovedVendor(**data.model_dump())
        self.db.add(vendor)
        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor

    async def list_vendors(self, component_id: str) -> list[ApprovedVendor]:
        result = await self.db.execute(
            select(ApprovedVendor)
            .where(ApprovedVendor.component_id == component_id)
            .order_by(ApprovedVendor.vendor_name)
        )
        return list(result.scalars().all())

    async def update_vendor(
        self, vendor_id: str, data: ApprovedVendorUpdate
    ) -> ApprovedVendor:
        result = await self.db.execute(
            select(ApprovedVendor).where(ApprovedVendor.id == vendor_id)
        )
        vendor = result.scalar_one_or_none()
        if not vendor:
            raise VendorNotFoundError(f"Vendor '{vendor_id}' not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(vendor, field, value)
        await self.db.commit()
        await self.db.refresh(vendor)
        return vendor
