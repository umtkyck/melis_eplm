"""Tests for engineering change management service."""

import pytest

from eplm.models.change import ChangeOrderStatus, ChangeRequestStatus
from eplm.schemas.change import (
    ChangeOrderCreate,
    ChangeOrderItemCreate,
    ChangeOrderUpdate,
    ChangeRequestCreate,
    ChangeRequestUpdate,
)
from eplm.services.change_service import ChangeService, InvalidStatusError


@pytest.fixture
def svc(db_session):
    return ChangeService(db_session)


@pytest.fixture
async def draft_ecr(svc):
    return await svc.create_ecr(
        ChangeRequestCreate(
            ecr_number="ECR-001",
            title="Replace obsolete capacitor",
            reason="Capacitor C5 is end-of-life",
            requested_by="engineer@example.com",
        )
    )


@pytest.fixture
async def approved_ecr(svc, draft_ecr):
    await svc.update_ecr(
        draft_ecr.id, ChangeRequestUpdate(status=ChangeRequestStatus.SUBMITTED)
    )
    await svc.update_ecr(
        draft_ecr.id, ChangeRequestUpdate(status=ChangeRequestStatus.UNDER_REVIEW)
    )
    return await svc.update_ecr(
        draft_ecr.id,
        ChangeRequestUpdate(
            status=ChangeRequestStatus.APPROVED, reviewed_by="lead@example.com"
        ),
    )


class TestECRWorkflow:
    async def test_create_ecr(self, svc, draft_ecr):
        assert draft_ecr.ecr_number == "ECR-001"
        assert draft_ecr.status == ChangeRequestStatus.DRAFT

    async def test_submit_ecr(self, svc, draft_ecr):
        updated = await svc.update_ecr(
            draft_ecr.id, ChangeRequestUpdate(status=ChangeRequestStatus.SUBMITTED)
        )
        assert updated.status == ChangeRequestStatus.SUBMITTED

    async def test_invalid_ecr_transition(self, svc, draft_ecr):
        with pytest.raises(InvalidStatusError):
            await svc.update_ecr(
                draft_ecr.id,
                ChangeRequestUpdate(status=ChangeRequestStatus.APPROVED),
            )

    async def test_full_approval_flow(self, svc, approved_ecr):
        assert approved_ecr.status == ChangeRequestStatus.APPROVED
        assert approved_ecr.reviewed_by == "lead@example.com"


class TestECOWorkflow:
    async def test_create_eco_requires_approved_ecr(self, svc, draft_ecr):
        with pytest.raises(InvalidStatusError):
            await svc.create_eco(
                ChangeOrderCreate(
                    eco_number="ECO-001",
                    change_request_id=draft_ecr.id,
                    title="Implement capacitor replacement",
                )
            )

    async def test_create_eco_from_approved_ecr(self, svc, approved_ecr):
        eco = await svc.create_eco(
            ChangeOrderCreate(
                eco_number="ECO-001",
                change_request_id=approved_ecr.id,
                title="Implement capacitor replacement",
                assigned_to="tech@example.com",
            )
        )
        assert eco.eco_number == "ECO-001"
        assert eco.status == ChangeOrderStatus.DRAFT

    async def test_eco_completion_flow(self, svc, approved_ecr):
        eco = await svc.create_eco(
            ChangeOrderCreate(
                eco_number="ECO-002",
                change_request_id=approved_ecr.id,
                title="Replace capacitor",
            )
        )
        eco = await svc.update_eco(
            eco.id, ChangeOrderUpdate(status=ChangeOrderStatus.PENDING_APPROVAL)
        )
        eco = await svc.update_eco(
            eco.id,
            ChangeOrderUpdate(
                status=ChangeOrderStatus.APPROVED, approved_by="manager@example.com"
            ),
        )
        assert eco.approved_at is not None
        eco = await svc.update_eco(
            eco.id, ChangeOrderUpdate(status=ChangeOrderStatus.IN_PROGRESS)
        )
        eco = await svc.update_eco(
            eco.id, ChangeOrderUpdate(status=ChangeOrderStatus.COMPLETED)
        )
        assert eco.status == ChangeOrderStatus.COMPLETED
        assert eco.completed_at is not None

    async def test_add_eco_item(self, svc, approved_ecr):
        eco = await svc.create_eco(
            ChangeOrderCreate(
                eco_number="ECO-003",
                change_request_id=approved_ecr.id,
                title="Update BOM",
            )
        )
        item = await svc.add_eco_item(
            eco.id,
            ChangeOrderItemCreate(
                item_type="component",
                item_id="some-component-id",
                from_revision="A",
                to_revision="B",
                change_description="Replace with new supplier part",
            ),
        )
        assert item.item_type == "component"
        assert item.from_revision == "A"
