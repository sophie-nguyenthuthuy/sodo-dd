"""Idempotent seed: creates a demo organization + owner user + API key."""

from __future__ import annotations

from app.core.security import generate_api_key, hash_password
from app.database import session_scope
from app.models import ApiKey, Organization, User
from app.models.organization import OrgTier, OrgType
from app.models.user import UserRole

DEMO_EMAIL = "demo@sodo-dd.local"
DEMO_PASSWORD = "demo_pa55word!"


def main() -> None:
    with session_scope() as db:
        org = db.query(Organization).filter_by(tax_code="0100000000").first()
        if org is None:
            org = Organization(
                id=Organization.new_id(),
                name="Demo Brokerage Co., Ltd.",
                tax_code="0100000000",
                type=OrgType.BROKER,
                tier=OrgTier.STANDARD,
                contact_email=DEMO_EMAIL,
            )
            db.add(org)
            db.flush()
            print(f"[seed] created organization {org.id}")

        user = db.query(User).filter_by(email=DEMO_EMAIL).first()
        if user is None:
            user = User(
                id=User.new_id(),
                organization_id=org.id,
                email=DEMO_EMAIL,
                full_name="Demo Owner",
                password_hash=hash_password(DEMO_PASSWORD),
                role=UserRole.OWNER,
            )
            db.add(user)
            print(f"[seed] created user {user.email} pw={DEMO_PASSWORD}")

        if not db.query(ApiKey).filter_by(organization_id=org.id, name="demo").first():
            raw, key_id, key_hash = generate_api_key(env="test")
            ak = ApiKey(
                id=ApiKey.new_id(),
                organization_id=org.id,
                name="demo",
                key_prefix=key_id,
                key_hash=key_hash,
            )
            db.add(ak)
            print(f"[seed] created API key (SHOW ONCE): {raw}")


if __name__ == "__main__":
    main()
