"""Engineering change request and change order management."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.change import (
    ChangeOrder,
    ChangeOrderItem,
    ChangeOrderStatus,
    ChangeRequest,
    ChangeRequestStatus,
)
from eplm.schemas.change import (
    ChangeOrderCreate,
    ChangeOrderItemCreate,
    ChangeOrderUpdate,
    ChangeRequestCreate,
    ChangeRequestUpdate,
)


class ChangeServiceError(Exception):
    pass


class ChangeRequestNotFoundError(ChangeServiceError):
    pass


class ChangeOrderNotFoundError(ChangeServiceError):
    pass


class InvalidStatusError(ChangeServiceError):
    pass


# Valid ECR status transitions
_ECR_TRANSITIONS: dict[ChangeRequestStatus, set[ChangeRequestStatus]] = {
    ChangeRequestStatus.DRAFT: {ChangeRequestStatus.SUBMITTED, ChangeRequestStatus.WITHDRAWN},
    ChangeRequestStatus.SUBMITTED: {ChangeRequestStatus.UNDER_REVIEW, ChangeRequestStatus.WITHDRAWN},
    ChangeRequestStatus.UNDER_REVIEW: {
        ChangeRequestStatus.APPROVED,
        ChangeRequestStatus.REJECTED,
    },
    ChangeRequestStatus.APPROVED: set(),
    ChangeRequestStatus.REJECTED: {ChangeRequestStatus.DRAFT},
    ChangeRequestStatus.WITHDRAWN: set(),
}

# Valid ECO status transitions
_ECO_TRANSITIONS: dict[ChangeOrderStatus, set[ChangeOrderStatus]] = {
    ChangeOrderStatus.DRAFT: {ChangeOrderStatus.PENDING_APPROVAL, ChangeOrderStatus.CANCELLED},
    ChangeOrderStatus.PENDING_APPROVAL: {
        ChangeOrderStatus.APPROVED,
        ChangeOrderStatus.DRAFT,
        ChangeOrderStatus.CANCELLED,
    },
    ChangeOrderStatus.APPROVED: {ChangeOrderStatus.IN_PROGRESS, ChangeOrderStatus.CANCELLED},
    ChangeOrderStatus.IN_PROGRESS: {ChangeOrderStatus.COMPLETED, ChangeOrderStatus.CANCELLED},
    ChangeOrderStatus.COMPLETED: set(),
    ChangeOrderStatus.CANCELLED: set(),
}


class ChangeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── ECR operations ──────────────────────────────────────────

    async def create_ecr(self, data: ChangeRequestCreate) -> ChangeRequest:
        ecr = ChangeRequest(**data.model_dump())
        self.db.add(ecr)
        await self.db.commit()
        await self.db.refresh(ecr)
        return ecr

    async def get_ecr(self, ecr_id: str) -> ChangeRequest:
        result = await self.db.execute(
            select(ChangeRequest)
            .options(selectinload(ChangeRequest.change_orders))
            .where(ChangeRequest.id == ecr_id)
        )
        ecr = result.scalar_one_or_none()
        if not ecr:
            raise ChangeRequestNotFoundError(f"ECR '{ecr_id}' not found")
        return ecr

    async def list_ecrs(
        self,
        status: ChangeRequestStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ChangeRequest]:
        query = select(ChangeRequest)
        if status:
            query = query.where(ChangeRequest.status == status)
        query = query.offset(offset).limit(limit).order_by(ChangeRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_ecr(
        self, ecr_id: str, data: ChangeRequestUpdate
    ) -> ChangeRequest:
        ecr = await self.get_ecr(ecr_id)
        update_data = data.model_dump(exclude_unset=True)

        # Validate status transition if status is being changed
        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            allowed = _ECR_TRANSITIONS.get(ecr.status, set())
            if new_status not in allowed:
                raise InvalidStatusError(
                    f"Cannot transition ECR from '{ecr.status.value}' to '{new_status.value}'"
                )

        for field, value in update_data.items():
            setattr(ecr, field, value)
        await self.db.commit()
        await self.db.refresh(ecr)
        return ecr

    # ── ECO operations ──────────────────────────────────────────

    async def create_eco(self, data: ChangeOrderCreate) -> ChangeOrder:
        # Verify the ECR exists and is approved
        ecr = await self.get_ecr(data.change_request_id)
        if ecr.status != ChangeRequestStatus.APPROVED:
            raise InvalidStatusError(
                "ECO can only be created for an approved ECR "
                f"(current status: {ecr.status.value})"
            )
        eco = ChangeOrder(**data.model_dump())
        self.db.add(eco)
        await self.db.commit()
        await self.db.refresh(eco)
        return eco

    async def get_eco(self, eco_id: str) -> ChangeOrder:
        result = await self.db.execute(
            select(ChangeOrder)
            .options(selectinload(ChangeOrder.items))
            .where(ChangeOrder.id == eco_id)
        )
        eco = result.scalar_one_or_none()
        if not eco:
            raise ChangeOrderNotFoundError(f"ECO '{eco_id}' not found")
        return eco

    async def list_ecos(
        self,
        status: ChangeOrderStatus | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ChangeOrder]:
        query = select(ChangeOrder)
        if status:
            query = query.where(ChangeOrder.status == status)
        query = query.offset(offset).limit(limit).order_by(ChangeOrder.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_eco(
        self, eco_id: str, data: ChangeOrderUpdate
    ) -> ChangeOrder:
        eco = await self.get_eco(eco_id)
        update_data = data.model_dump(exclude_unset=True)

        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            allowed = _ECO_TRANSITIONS.get(eco.status, set())
            if new_status not in allowed:
                raise InvalidStatusError(
                    f"Cannot transition ECO from '{eco.status.value}' to '{new_status.value}'"
                )
            # Set timestamps on approval / completion
            if new_status == ChangeOrderStatus.APPROVED:
                eco.approved_at = datetime.now(timezone.utc)
                if "approved_by" in update_data:
                    eco.approved_by = update_data.pop("approved_by")
            if new_status == ChangeOrderStatus.COMPLETED:
                eco.completed_at = datetime.now(timezone.utc)

        for field, value in update_data.items():
            setattr(eco, field, value)
        await self.db.commit()
        await self.db.refresh(eco)
        return eco

    async def add_eco_item(
        self, eco_id: str, data: ChangeOrderItemCreate
    ) -> ChangeOrderItem:
        await self.get_eco(eco_id)  # verify exists
        item = ChangeOrderItem(change_order_id=eco_id, **data.model_dump())
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item
