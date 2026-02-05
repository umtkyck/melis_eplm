"""Configurable approval workflow engine.

Addresses IFS complaints:
- "No automatic approval routines"
- "Permission workflow really does not make much sense"
- "Must manually create one for every situation"

This engine lets users define reusable approval templates, launch approval
requests against any entity, and progress through multi-step approval chains.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eplm.models.approval import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalTemplate,
    ApprovalTemplateStep,
)
from eplm.schemas.approval import (
    ApprovalDecisionCreate,
    ApprovalRequestCreate,
    ApprovalTemplateCreate,
)


class ApprovalServiceError(Exception):
    pass


class TemplateNotFoundError(ApprovalServiceError):
    pass


class RequestNotFoundError(ApprovalServiceError):
    pass


class WorkflowError(ApprovalServiceError):
    pass


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Templates ────────────────────────────────────────────────

    async def create_template(self, data: ApprovalTemplateCreate) -> ApprovalTemplate:
        template = ApprovalTemplate(
            name=data.name,
            entity_type=data.entity_type,
            description=data.description,
        )
        self.db.add(template)
        await self.db.flush()

        for step_data in data.steps:
            step = ApprovalTemplateStep(
                template_id=template.id,
                step_order=step_data.step_order,
                role=step_data.role,
                approver=step_data.approver,
                is_required=step_data.is_required,
                auto_approve_after_hours=step_data.auto_approve_after_hours,
            )
            self.db.add(step)

        await self.db.commit()
        return await self.get_template(template.id)

    async def get_template(self, template_id: str) -> ApprovalTemplate:
        result = await self.db.execute(
            select(ApprovalTemplate)
            .options(selectinload(ApprovalTemplate.steps))
            .where(ApprovalTemplate.id == template_id)
            .execution_options(populate_existing=True)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise TemplateNotFoundError(f"Approval template '{template_id}' not found")
        return template

    async def list_templates(
        self, entity_type: str | None = None
    ) -> list[ApprovalTemplate]:
        query = select(ApprovalTemplate).options(selectinload(ApprovalTemplate.steps))
        if entity_type:
            query = query.where(ApprovalTemplate.entity_type == entity_type)
        query = query.order_by(ApprovalTemplate.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── Requests ─────────────────────────────────────────────────

    async def start_approval(self, data: ApprovalRequestCreate) -> ApprovalRequest:
        """Launch an approval workflow for an entity, optionally from a template."""
        request = ApprovalRequest(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            template_id=data.template_id,
            title=data.title,
            current_step=1,
        )
        self.db.add(request)
        await self.db.flush()

        # If a template is provided, pre-populate decision slots
        if data.template_id:
            template = await self.get_template(data.template_id)
            for step in template.steps:
                decision = ApprovalDecision(
                    request_id=request.id,
                    step_order=step.step_order,
                    role=step.role,
                    status=ApprovalStatus.PENDING,
                )
                self.db.add(decision)

        await self.db.commit()
        return await self.get_request(request.id)

    async def get_request(self, request_id: str) -> ApprovalRequest:
        result = await self.db.execute(
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.decisions))
            .where(ApprovalRequest.id == request_id)
            .execution_options(populate_existing=True)
        )
        req = result.scalar_one_or_none()
        if not req:
            raise RequestNotFoundError(f"Approval request '{request_id}' not found")
        return req

    async def list_pending(self, entity_type: str | None = None) -> list[ApprovalRequest]:
        query = (
            select(ApprovalRequest)
            .options(selectinload(ApprovalRequest.decisions))
            .where(ApprovalRequest.is_complete.is_(False))
        )
        if entity_type:
            query = query.where(ApprovalRequest.entity_type == entity_type)
        query = query.order_by(ApprovalRequest.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def submit_decision(
        self, request_id: str, data: ApprovalDecisionCreate
    ) -> ApprovalRequest:
        """Record an approval/rejection decision for the current step."""
        request = await self.get_request(request_id)

        if request.is_complete:
            raise WorkflowError("This approval request is already complete")

        # Find the current step's decision slot
        current_decision = None
        for d in request.decisions:
            if d.step_order == request.current_step and d.status == ApprovalStatus.PENDING:
                current_decision = d
                break

        if not current_decision:
            # No pre-populated slot — create one ad-hoc
            current_decision = ApprovalDecision(
                request_id=request_id,
                step_order=request.current_step,
                role="ad_hoc",
                status=ApprovalStatus.PENDING,
            )
            self.db.add(current_decision)
            await self.db.flush()

        current_decision.decided_by = data.decided_by
        current_decision.status = data.status
        current_decision.comment = data.comment

        if data.status == ApprovalStatus.REJECTED:
            request.is_complete = True
            request.is_approved = False
        elif data.status in (ApprovalStatus.APPROVED, ApprovalStatus.SKIPPED):
            # Check if there are more steps
            remaining = [
                d for d in request.decisions
                if d.step_order > request.current_step and d.status == ApprovalStatus.PENDING
            ]
            if remaining:
                request.current_step = remaining[0].step_order
            else:
                request.is_complete = True
                request.is_approved = True

        await self.db.commit()
        return await self.get_request(request_id)
