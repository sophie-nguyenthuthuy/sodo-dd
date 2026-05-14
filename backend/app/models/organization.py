from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.certificate import Certificate
    from app.models.user import User


import enum


class OrgType(enum.StrEnum):
    BROKER = "broker"
    LAW_FIRM = "law_firm"
    BANK = "bank"
    INDIVIDUAL = "individual"


class OrgTier(enum.StrEnum):
    TRIAL = "trial"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"


class Organization(Base, IDMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tax_code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    type: Mapped[OrgType] = mapped_column(Enum(OrgType, name="org_type"), default=OrgType.BROKER)
    tier: Mapped[OrgTier] = mapped_column(Enum(OrgTier, name="org_tier"), default=OrgTier.TRIAL)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(40))

    users: Mapped[list["User"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    certificates: Mapped[list["Certificate"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )

    @staticmethod
    def new_id() -> str:
        return new_ulid("org")
