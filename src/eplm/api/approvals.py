"""Approval workflow API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.schemas.approval import (
    ApprovalDecisionCreate,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalTemplateCreate,
    ApprovalTemplateResponse,
)
from eplm.services.approval_service import (
    ApprovalService,
    RequestNotFoundError,
    TemplateNotFoundError,
    WorkflowError,
)

router = APIRouter(prefix="/approvals", tags=["approvals"])


def _svc(db: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


# ── Templates ────────────────────────────────────────────────────

@router.post("/templates", response_model=ApprovalTemplateResponse, status_code=201)
async def create_template(
    data: ApprovalTemplateCreate, svc: ApprovalService = Depends(_svc)
):
    return await svc.create_template(data)


@router.get("/templates", response_model=list[ApprovalTemplateResponse])
async def list_templates(
    entity_type: str | None = None, svc: ApprovalService = Depends(_svc)
):
    return await svc.list_templates(entity_type=entity_type)


@router.get("/templates/{template_id}", response_model=ApprovalTemplateResponse)
async def get_template(
    template_id: str, svc: ApprovalService = Depends(_svc)
):
    try:
        return await svc.get_template(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(404, str(e))


# ── Requests ─────────────────────────────────────────────────────

@router.post("/requests", response_model=ApprovalRequestResponse, status_code=201)
async def start_approval(
    data: ApprovalRequestCreate, svc: ApprovalService = Depends(_svc)
):
    try:
        return await svc.start_approval(data)
    except TemplateNotFoundError as e:
        raise HTTPException(404, str(e))


@router.get("/requests/pending", response_model=list[ApprovalRequestResponse])
async def list_pending_approvals(
    entity_type: str | None = None, svc: ApprovalService = Depends(_svc)
):
    return await svc.list_pending(entity_type=entity_type)


@router.get("/requests/{request_id}", response_model=ApprovalRequestResponse)
async def get_request(
    request_id: str, svc: ApprovalService = Depends(_svc)
):
    try:
        return await svc.get_request(request_id)
    except RequestNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post(
    "/requests/{request_id}/decide",
    response_model=ApprovalRequestResponse,
)
async def submit_decision(
    request_id: str,
    data: ApprovalDecisionCreate,
    svc: ApprovalService = Depends(_svc),
):
    try:
        return await svc.submit_decision(request_id, data)
    except RequestNotFoundError as e:
        raise HTTPException(404, str(e))
    except WorkflowError as e:
        raise HTTPException(400, str(e))
