from datetime import UTC, datetime

import ulid
from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def new_ulid(prefix: str) -> str:
    return f"{prefix}_{ulid.new().str}"


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        # CamelCase -> snake_case, plural-naive
        import re

        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class IDMixin:
    """ULID primary key as string (26 chars) prefixed by entity type."""

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
