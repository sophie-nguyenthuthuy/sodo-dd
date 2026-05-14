from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.exceptions import Forbidden, RateLimited, Unauthorized
from app.core.rate_limit import check_rate_limit
from app.core.security import decode_token, hash_api_key
from app.database import get_db
from app.models import ApiKey, Organization, User


def get_session(db: Session = Depends(get_db)) -> Session:
    return db


SessionDep = Annotated[Session, Depends(get_session)]


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise Unauthorized("missing bearer token")
    return authorization.split(" ", 1)[1].strip()


def current_api_key(
    request: Request,
    db: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> ApiKey:
    raw = _bearer(authorization)
    if not raw.startswith("sk_"):
        raise Unauthorized("invalid api key format")
    ak = db.query(ApiKey).filter(ApiKey.key_hash == hash_api_key(raw)).first()
    if ak is None or not ak.is_active or ak.revoked_at is not None:
        raise Unauthorized("invalid api key")

    allowed, _ = check_rate_limit(f"ak:{ak.id}")
    if not allowed:
        raise RateLimited("API key rate limit exceeded")

    ak.last_used_at = datetime.now(UTC)
    db.add(ak)
    db.commit()
    request.state.actor_id = ak.id
    request.state.actor_type = "api_key"
    request.state.organization_id = ak.organization_id
    return ak


ApiKeyDep = Annotated[ApiKey, Depends(current_api_key)]


def current_user(
    request: Request,
    db: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    raw = _bearer(authorization)
    try:
        payload = decode_token(raw)
    except Exception as exc:
        raise Unauthorized("invalid token") from exc
    if payload.get("typ") != "access":
        raise Unauthorized("wrong token type")
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise Unauthorized("user not found or disabled")
    request.state.actor_id = user.id
    request.state.actor_type = "user"
    request.state.organization_id = user.organization_id
    return user


UserDep = Annotated[User, Depends(current_user)]


def require_org(ak: ApiKeyDep, db: SessionDep) -> Organization:
    org = db.get(Organization, ak.organization_id)
    if org is None:
        raise Forbidden("organization missing")
    return org


OrgDep = Annotated[Organization, Depends(require_org)]
