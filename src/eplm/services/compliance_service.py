"""Compliance and regulatory tracking service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.models.compliance import ComplianceRecord, ComplianceStandard, ComplianceStatus
from eplm.schemas.compliance import (
    ComplianceRecordCreate,
    ComplianceRecordUpdate,
    ComplianceStandardCreate,
)


class ComplianceServiceError(Exception):
    pass


class StandardNotFoundError(ComplianceServiceError):
    pass


class RecordNotFoundError(ComplianceServiceError):
    pass


class ComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Standards ────────────────────────────────────────────────

    async def create_standard(self, data: ComplianceStandardCreate) -> ComplianceStandard:
        standard = ComplianceStandard(**data.model_dump())
        self.db.add(standard)
        await self.db.commit()
        await self.db.refresh(standard)
        return standard

    async def get_standard(self, standard_id: str) -> ComplianceStandard:
        result = await self.db.execute(
            select(ComplianceStandard).where(ComplianceStandard.id == standard_id)
        )
        standard = result.scalar_one_or_none()
        if not standard:
            raise StandardNotFoundError(f"Standard '{standard_id}' not found")
        return standard

    async def list_standards(self) -> list[ComplianceStandard]:
        result = await self.db.execute(
            select(ComplianceStandard).order_by(ComplianceStandard.code)
        )
        return list(result.scalars().all())

    # ── Records ─────────────────────────────────────────────────

    async def create_record(self, data: ComplianceRecordCreate) -> ComplianceRecord:
        record = ComplianceRecord(**data.model_dump())
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_record(self, record_id: str) -> ComplianceRecord:
        result = await self.db.execute(
            select(ComplianceRecord).where(ComplianceRecord.id == record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise RecordNotFoundError(f"Compliance record '{record_id}' not found")
        return record

    async def list_records_for_product(
        self, product_id: str
    ) -> list[ComplianceRecord]:
        result = await self.db.execute(
            select(ComplianceRecord)
            .where(ComplianceRecord.product_id == product_id)
            .order_by(ComplianceRecord.created_at)
        )
        return list(result.scalars().all())

    async def update_record(
        self, record_id: str, data: ComplianceRecordUpdate
    ) -> ComplianceRecord:
        record = await self.get_record(record_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(record, field, value)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_compliance_summary(self, product_id: str) -> dict:
        """Get a compliance status summary for a product."""
        records = await self.list_records_for_product(product_id)
        summary = {
            "product_id": product_id,
            "total_standards": len(records),
            "passed": 0,
            "failed": 0,
            "in_progress": 0,
            "not_started": 0,
            "expired": 0,
            "records": [],
        }
        for record in records:
            summary["records"].append(
                {
                    "standard_id": record.standard_id,
                    "status": record.status.value,
                    "is_valid": record.is_valid,
                }
            )
            if record.status == ComplianceStatus.PASSED:
                if record.is_valid:
                    summary["passed"] += 1
                else:
                    summary["expired"] += 1
            elif record.status == ComplianceStatus.FAILED:
                summary["failed"] += 1
            elif record.status == ComplianceStatus.IN_PROGRESS:
                summary["in_progress"] += 1
            elif record.status == ComplianceStatus.NOT_STARTED:
                summary["not_started"] += 1

        return summary
