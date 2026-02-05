"""Pydantic schemas for webhook subscriptions."""

from datetime import datetime

from pydantic import BaseModel, Field

from eplm.models.webhook import WebhookEvent


class WebhookSubscriptionCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=500)
    event: WebhookEvent
    secret: str = ""
    description: str = ""


class WebhookSubscriptionResponse(BaseModel):
    id: str
    url: str
    event: WebhookEvent
    description: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
