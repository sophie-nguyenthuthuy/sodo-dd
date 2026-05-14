from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid


class AuditLog(Base, IDMixin, TimestampMixin):
    """Immutable audit trail for compliance (NĐ 13/2023, SBV TT 41/2016)."""

    organization_id: Mapped[str | None] = mapped_column(
        ForeignKey("organization.id", ondelete="SET NULL"), index=True
    )
    actor_id: Mapped[str | None] = mapped_column(String(40), index=True)     # user_id or api_key_id
    actor_type: Mapped[str] = mapped_column(String(20))                       # user | api_key | system
    action: Mapped[str] = mapped_column(String(80), index=True)               # cert.view, dd.create, ...
    resource_type: Mapped[str | None] = mapped_column(String(40), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(40), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)

    @staticmethod
    def new_id() -> str:
        return new_ulid("log")
