from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid


class WebhookEndpoint(Base, IDMixin, TimestampMixin):
    organization_id: Mapped[str] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    events: Mapped[str] = mapped_column(String(500), default="dd.completed,dd.failed")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    @staticmethod
    def new_id() -> str:
        return new_ulid("whk")
