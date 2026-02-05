"""Webhook subscription management API."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from eplm.database import get_db
from eplm.models.webhook import WebhookEvent, WebhookSubscription
from eplm.schemas.webhook import WebhookSubscriptionCreate, WebhookSubscriptionResponse

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookSubscriptionResponse, status_code=201)
async def create_webhook(
    data: WebhookSubscriptionCreate, db: AsyncSession = Depends(get_db)
):
    webhook = WebhookSubscription(**data.model_dump())
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    return webhook


@router.get("", response_model=list[WebhookSubscriptionResponse])
async def list_webhooks(
    event: WebhookEvent | None = None, db: AsyncSession = Depends(get_db)
):
    query = select(WebhookSubscription).where(WebhookSubscription.is_active.is_(True))
    if event:
        query = query.where(WebhookSubscription.event == event)
    result = await db.execute(query.order_by(WebhookSubscription.created_at))
    return list(result.scalars().all())


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
    )
    webhook = result.scalar_one_or_none()
    if not webhook:
        raise HTTPException(404, f"Webhook '{webhook_id}' not found")
    await db.delete(webhook)
    await db.commit()
