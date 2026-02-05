"""BOM management — creation, line-item manipulation, cost roll-up."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.bom import BillOfMaterials, BomLineItem
from eplm.schemas.bom import BomCreate, BomLineItemCreate


class BomServiceError(Exception):
    pass


class BomNotFoundError(BomServiceError):
    pass


class LineItemConflictError(BomServiceError):
    pass


class BomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: BomCreate) -> BillOfMaterials:
        bom = BillOfMaterials(**data.model_dump())
        self.db.add(bom)
        await self.db.commit()
        # Re-fetch with line_items loaded so properties (total_cost, etc.) work
        return await self.get(bom.id)

    async def get(self, bom_id: str) -> BillOfMaterials:
        result = await self.db.execute(
            select(BillOfMaterials)
            .options(selectinload(BillOfMaterials.line_items))
            .where(BillOfMaterials.id == bom_id)
            .execution_options(populate_existing=True)
        )
        bom = result.scalar_one_or_none()
        if not bom:
            raise BomNotFoundError(f"BOM '{bom_id}' not found")
        return bom

    async def list_for_product(self, product_id: str) -> list[BillOfMaterials]:
        result = await self.db.execute(
            select(BillOfMaterials)
            .options(selectinload(BillOfMaterials.line_items))
            .where(BillOfMaterials.product_id == product_id)
            .order_by(BillOfMaterials.revision)
        )
        return list(result.scalars().all())

    async def add_line_item(
        self, bom_id: str, data: BomLineItemCreate
    ) -> BomLineItem:
        bom = await self.get(bom_id)
        # Check for duplicate reference designator
        for item in bom.line_items:
            if item.reference == data.reference:
                raise LineItemConflictError(
                    f"Reference '{data.reference}' already exists in BOM"
                )
        line_item = BomLineItem(bom_id=bom_id, **data.model_dump())
        self.db.add(line_item)
        await self.db.commit()
        await self.db.refresh(line_item)
        return line_item

    async def remove_line_item(self, line_item_id: str) -> None:
        result = await self.db.execute(
            select(BomLineItem).where(BomLineItem.id == line_item_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            raise BomNotFoundError(f"Line item '{line_item_id}' not found")
        await self.db.delete(item)
        await self.db.commit()

    async def get_cost_summary(self, bom_id: str) -> dict:
        """Return a cost breakdown for the BOM."""
        bom = await self.get(bom_id)
        items = []
        for li in bom.line_items:
            items.append(
                {
                    "reference": li.reference,
                    "component_id": li.component_id,
                    "quantity": li.quantity,
                    "unit_cost": li.unit_cost,
                    "line_cost": li.line_cost,
                    "do_not_populate": li.do_not_populate,
                }
            )
        return {
            "bom_id": bom.id,
            "revision": bom.revision,
            "total_cost": bom.total_cost,
            "component_count": bom.component_count,
            "line_items": items,
        }

    async def clone_bom(
        self, bom_id: str, new_revision: str
    ) -> BillOfMaterials:
        """Clone an existing BOM to a new revision, copying all line items."""
        source = await self.get(bom_id)
        new_bom = BillOfMaterials(
            product_id=source.product_id,
            revision=new_revision,
            name=source.name,
            description=source.description,
            phase=source.phase,
        )
        self.db.add(new_bom)
        await self.db.flush()  # get new_bom.id

        for item in source.line_items:
            new_item = BomLineItem(
                bom_id=new_bom.id,
                component_id=item.component_id,
                reference=item.reference,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                notes=item.notes,
                do_not_populate=item.do_not_populate,
            )
            self.db.add(new_item)

        await self.db.commit()
        return await self.get(new_bom.id)

    async def delete(self, bom_id: str) -> None:
        bom = await self.get(bom_id)
        await self.db.delete(bom)
        await self.db.commit()
