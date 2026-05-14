from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["due_diligence:read", "due_diligence:write"])


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str  # raw key — shown once
    key_prefix: str
    scopes: list[str]
