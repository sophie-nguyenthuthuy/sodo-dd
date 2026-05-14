from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid

if TYPE_CHECKING:
    from app.models.organization import Organization


class ApiKey(Base, IDMixin, TimestampMixin):
    organization_id: Mapped[str] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str] = mapped_column(String(500), default="due_diligence:read,due_diligence:write")

    organization: Mapped["Organization"] = relationship(back_populates="api_keys")

    @staticmethod
    def new_id() -> str:
        return new_ulid("ak")
