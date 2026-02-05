"""Product lifecycle and CRUD operations."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.lifecycle import LifecyclePhase, can_transition
from eplm.models.product import Product, ProductRevision
from eplm.schemas.product import (
    PhaseTransitionRequest,
    ProductCreate,
    ProductRevisionCreate,
    ProductUpdate,
)


class ProductServiceError(Exception):
    pass


class ProductNotFoundError(ProductServiceError):
    pass


class InvalidTransitionError(ProductServiceError):
    pass


class DuplicatePartNumberError(ProductServiceError):
    pass


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ProductCreate) -> Product:
        existing = await self.db.execute(
            select(Product).where(Product.part_number == data.part_number)
        )
        if existing.scalar_one_or_none():
            raise DuplicatePartNumberError(
                f"Part number '{data.part_number}' already exists"
            )

        product = Product(**data.model_dump())
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get(self, product_id: str) -> Product:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.revisions),
                selectinload(Product.boms),
                selectinload(Product.documents),
                selectinload(Product.compliance_records),
            )
            .where(Product.id == product_id)
            .execution_options(populate_existing=True)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise ProductNotFoundError(f"Product '{product_id}' not found")
        return product

    async def get_by_part_number(self, part_number: str) -> Product:
        result = await self.db.execute(
            select(Product).where(Product.part_number == part_number)
        )
        product = result.scalar_one_or_none()
        if not product:
            raise ProductNotFoundError(
                f"Product with part number '{part_number}' not found"
            )
        return product

    async def list_all(
        self,
        phase: LifecyclePhase | None = None,
        category: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        query = select(Product)
        if phase:
            query = query.where(Product.phase == phase)
        if category:
            query = query.where(Product.category == category)
        query = query.offset(offset).limit(limit).order_by(Product.part_number)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, product_id: str, data: ProductUpdate) -> Product:
        product = await self.get(product_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def transition_phase(
        self, product_id: str, request: PhaseTransitionRequest
    ) -> Product:
        """Move a product to a new lifecycle phase, enforcing valid transitions."""
        product = await self.get(product_id)
        if not can_transition(product.phase, request.target_phase):
            raise InvalidTransitionError(
                f"Cannot transition from '{product.phase.value}' "
                f"to '{request.target_phase.value}'"
            )
        product.phase = request.target_phase
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def create_revision(
        self, product_id: str, data: ProductRevisionCreate, released_by: str = ""
    ) -> ProductRevision:
        product = await self.get(product_id)
        revision = ProductRevision(
            product_id=product.id,
            revision=data.revision,
            change_summary=data.change_summary,
            phase_at_creation=product.phase,
            released_at=datetime.now(timezone.utc),
            released_by=released_by,
        )
        self.db.add(revision)
        await self.db.commit()
        await self.db.refresh(revision)
        return revision

    async def get_revisions(self, product_id: str) -> list[ProductRevision]:
        product = await self.get(product_id)
        return list(product.revisions)

    async def delete(self, product_id: str) -> None:
        product = await self.get(product_id)
        await self.db.delete(product)
        await self.db.commit()
