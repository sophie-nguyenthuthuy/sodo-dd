import secrets

from fastapi import APIRouter, status
from pydantic import BaseModel, HttpUrl

from app.api.deps import ApiKeyDep, SessionDep
from app.core.exceptions import NotFound
from app.models import WebhookEndpoint
from app.schemas.common import ORMModel

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[str] = ["dd.completed", "dd.failed"]


class WebhookOut(ORMModel):
    id: str
    url: str
    events: str
    is_active: bool
    secret: str | None = None  # only on create


@router.post("", response_model=WebhookOut, status_code=status.HTTP_201_CREATED)
def create_webhook(req: WebhookCreate, db: SessionDep, ak: ApiKeyDep) -> WebhookOut:
    secret = secrets.token_urlsafe(32)
    wh = WebhookEndpoint(
        id=WebhookEndpoint.new_id(),
        organization_id=ak.organization_id,
        url=str(req.url),
        secret=secret,
        events=",".join(req.events),
    )
    db.add(wh)
    db.commit()
    return WebhookOut(id=wh.id, url=wh.url, events=wh.events, is_active=wh.is_active, secret=secret)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(webhook_id: str, db: SessionDep, ak: ApiKeyDep) -> None:
    wh = db.get(WebhookEndpoint, webhook_id)
    if wh is None or wh.organization_id != ak.organization_id:
        raise NotFound("webhook not found")
    db.delete(wh)
    db.commit()
