from fastapi import APIRouter, status

from app.api.deps import SessionDep, UserDep
from app.config import settings
from app.core.exceptions import Forbidden, Unauthorized
from app.core.security import generate_api_key, issue_access_token, verify_password
from app.models import ApiKey, User
from app.models.user import UserRole
from app.schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: SessionDep) -> TokenResponse:
    user = db.query(User).filter(User.email == req.email).first()
    if user is None or not user.is_active or not verify_password(req.password, user.password_hash):
        raise Unauthorized("invalid credentials")
    token = issue_access_token(
        user.id, claims={"org": user.organization_id, "role": user.role.value}
    )
    return TokenResponse(access_token=token, expires_in=settings.jwt_access_ttl_min * 60)


@router.post("/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(req: ApiKeyCreateRequest, db: SessionDep, user: UserDep) -> ApiKeyCreateResponse:
    if user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise Forbidden("only owner/admin may create API keys")
    raw, key_id, key_hash = generate_api_key(env="live" if settings.is_production else "test")
    ak = ApiKey(
        id=ApiKey.new_id(),
        organization_id=user.organization_id,
        name=req.name,
        key_prefix=key_id,
        key_hash=key_hash,
        scopes=",".join(req.scopes),
    )
    db.add(ak)
    db.commit()
    return ApiKeyCreateResponse(
        id=ak.id, name=ak.name, key=raw, key_prefix=ak.key_prefix, scopes=req.scopes
    )
