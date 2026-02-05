"""Tests for the approval workflow engine."""

import pytest

from eplm.models.approval import ApprovalStatus
from eplm.schemas.approval import (
    ApprovalDecisionCreate,
    ApprovalRequestCreate,
    ApprovalTemplateCreate,
    ApprovalTemplateStepCreate,
)
from eplm.services.approval_service import ApprovalService, WorkflowError


@pytest.fixture
def svc(db_session):
    return ApprovalService(db_session)


@pytest.fixture
async def ecr_template(svc):
    return await svc.create_template(
        ApprovalTemplateCreate(
            name="ECR Approval",
            entity_type="ecr",
            description="Standard ECR approval chain",
            steps=[
                ApprovalTemplateStepCreate(step_order=1, role="design_lead"),
                ApprovalTemplateStepCreate(step_order=2, role="quality_engineer"),
                ApprovalTemplateStepCreate(step_order=3, role="engineering_manager"),
            ],
        )
    )


class TestApprovalTemplates:
    async def test_create_template_with_steps(self, svc, ecr_template):
        assert ecr_template.name == "ECR Approval"
        assert len(ecr_template.steps) == 3
        assert ecr_template.steps[0].role == "design_lead"
        assert ecr_template.steps[2].role == "engineering_manager"

    async def test_list_templates_by_entity_type(self, svc, ecr_template):
        templates = await svc.list_templates(entity_type="ecr")
        assert len(templates) == 1

        templates = await svc.list_templates(entity_type="nonexistent")
        assert len(templates) == 0


class TestApprovalWorkflow:
    async def test_start_approval_from_template(self, svc, ecr_template):
        request = await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="test-ecr-id",
                template_id=ecr_template.id,
                title="Approve ECR-001",
            )
        )
        assert request.current_step == 1
        assert request.is_complete is False
        assert len(request.decisions) == 3

    async def test_approve_step_advances(self, svc, ecr_template):
        request = await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="test-ecr-2",
                template_id=ecr_template.id,
                title="Approve ECR-002",
            )
        )
        # Approve step 1
        request = await svc.submit_decision(
            request.id,
            ApprovalDecisionCreate(
                decided_by="alice@example.com",
                status=ApprovalStatus.APPROVED,
                comment="Design looks good",
            ),
        )
        assert request.current_step == 2
        assert request.is_complete is False

    async def test_full_approval_chain(self, svc, ecr_template):
        request = await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="test-ecr-3",
                template_id=ecr_template.id,
                title="Approve ECR-003",
            )
        )
        for approver in ["alice@ex.com", "bob@ex.com", "charlie@ex.com"]:
            request = await svc.submit_decision(
                request.id,
                ApprovalDecisionCreate(
                    decided_by=approver,
                    status=ApprovalStatus.APPROVED,
                ),
            )
        assert request.is_complete is True
        assert request.is_approved is True

    async def test_rejection_stops_chain(self, svc, ecr_template):
        request = await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="test-ecr-4",
                template_id=ecr_template.id,
                title="Approve ECR-004",
            )
        )
        request = await svc.submit_decision(
            request.id,
            ApprovalDecisionCreate(
                decided_by="alice@ex.com",
                status=ApprovalStatus.REJECTED,
                comment="Needs rework",
            ),
        )
        assert request.is_complete is True
        assert request.is_approved is False

    async def test_cannot_decide_on_completed_request(self, svc, ecr_template):
        request = await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="test-ecr-5",
                template_id=ecr_template.id,
                title="Approve ECR-005",
            )
        )
        # Reject immediately
        request = await svc.submit_decision(
            request.id,
            ApprovalDecisionCreate(
                decided_by="alice@ex.com",
                status=ApprovalStatus.REJECTED,
            ),
        )
        with pytest.raises(WorkflowError):
            await svc.submit_decision(
                request.id,
                ApprovalDecisionCreate(
                    decided_by="bob@ex.com",
                    status=ApprovalStatus.APPROVED,
                ),
            )

    async def test_list_pending(self, svc, ecr_template):
        await svc.start_approval(
            ApprovalRequestCreate(
                entity_type="ecr",
                entity_id="pending-1",
                template_id=ecr_template.id,
                title="Pending 1",
            )
        )
        pending = await svc.list_pending(entity_type="ecr")
        assert len(pending) >= 1
