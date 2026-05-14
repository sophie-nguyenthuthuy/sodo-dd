import json
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.security import sign_webhook
from app.logging import get_logger
from app.models import WebhookEndpoint

log = get_logger("webhooks")


@retry(stop=stop_after_attempt(4), wait=wait_exponential(min=1, max=15), reraise=False)
def deliver_event(wh: WebhookEndpoint, event: str, payload: dict[str, Any]) -> None:
    body = json.dumps(
        {"event": event, "data": payload, "at": datetime.now(UTC).isoformat()}
    ).encode()
    ts = int(datetime.now(UTC).timestamp())
    signature = sign_webhook(wh.secret, body, ts)
    try:
        with httpx.Client(timeout=10) as c:
            r = c.post(
                wh.url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Sodo-Event": event,
                    "X-Sodo-Signature": signature,
                },
            )
            r.raise_for_status()
    except Exception:
        log.exception("webhook delivery failed", url=wh.url, event=event)
        raise
