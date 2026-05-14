"""Auth primitives: password hashing, JWT, API keys, field-level encryption."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ───── Passwords
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ───── JWT
def issue_access_token(subject: str, *, claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_min)).timestamp()),
        "typ": "access",
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


# ───── API keys
# Format: sk_<env>_<random>; stored as HMAC-SHA256(secret_key, raw_key)
def generate_api_key(env: str = "live") -> tuple[str, str, str]:
    """Returns (raw_key, key_id, key_hash). raw_key shown once to user."""
    raw_random = secrets.token_urlsafe(32)
    raw = f"{settings.api_key_prefix}{env}_{raw_random}"
    key_id = raw[: len(settings.api_key_prefix) + len(env) + 1 + 8]  # human-friendly prefix
    return raw, key_id, hash_api_key(raw)


def hash_api_key(raw: str) -> str:
    return hmac.new(settings.secret_key.encode(), raw.encode(), hashlib.sha256).hexdigest()


def verify_api_key(raw: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw), stored_hash)


# ───── Field-level encryption (AES-GCM)
def _aesgcm() -> AESGCM:
    key_b64 = settings.field_encryption_key
    if key_b64.startswith("base64:"):
        key_b64 = key_b64[len("base64:") :]
    key = base64.b64decode(key_b64)
    if len(key) not in (16, 24, 32):
        raise ValueError("FIELD_ENCRYPTION_KEY must decode to 16/24/32 bytes")
    return AESGCM(key)


def encrypt_field(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    aes = _aesgcm()
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode(), associated_data=settings.field_encryption_key_id.encode())
    return base64.b64encode(nonce + ct).decode()


def decrypt_field(ciphertext: str | None) -> str | None:
    if ciphertext is None:
        return None
    aes = _aesgcm()
    blob = base64.b64decode(ciphertext)
    nonce, ct = blob[:12], blob[12:]
    return aes.decrypt(nonce, ct, associated_data=settings.field_encryption_key_id.encode()).decode()


# ───── Webhook HMAC
def sign_webhook(secret: str, body: bytes, timestamp: int) -> str:
    msg = f"{timestamp}.".encode() + body
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={sig}"


def verify_webhook(secret: str, body: bytes, header: str, *, tolerance_sec: int = 300) -> bool:
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts = int(parts["t"])
        provided = parts["v1"]
    except Exception:
        return False
    if abs(int(datetime.now(UTC).timestamp()) - ts) > tolerance_sec:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, expected)
