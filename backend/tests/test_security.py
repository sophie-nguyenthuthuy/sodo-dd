from app.core.security import (
    decrypt_field,
    encrypt_field,
    generate_api_key,
    hash_api_key,
    hash_password,
    sign_webhook,
    verify_api_key,
    verify_password,
    verify_webhook,
)


def test_password_roundtrip():
    h = hash_password("super-secret-123")
    assert verify_password("super-secret-123", h)
    assert not verify_password("wrong", h)


def test_api_key_roundtrip():
    raw, key_id, stored = generate_api_key(env="test")
    assert raw.startswith("sk_test_")
    assert key_id.startswith("sk_test_")
    assert verify_api_key(raw, stored)
    assert not verify_api_key("sk_test_zzz", stored)
    # Stable hash
    assert hash_api_key(raw) == stored


def test_field_encryption_roundtrip():
    ct = encrypt_field("Nguyễn Văn A — CCCD 012345678901")
    assert ct is not None and ct != "Nguyễn Văn A — CCCD 012345678901"
    assert decrypt_field(ct) == "Nguyễn Văn A — CCCD 012345678901"
    assert encrypt_field(None) is None
    assert decrypt_field(None) is None


def test_webhook_signature():
    import time

    body = b'{"event":"dd.completed"}'
    ts = int(time.time())
    sig = sign_webhook("shh", body, ts)
    assert verify_webhook("shh", body, sig)
    assert not verify_webhook("wrong", body, sig)
