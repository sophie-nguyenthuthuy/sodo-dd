"""Sổ Đỏ / Sổ Hồng certificate record."""

import enum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid

if TYPE_CHECKING:
    from app.models.organization import Organization


class CertificateForm(enum.StrEnum):
    SO_DO_1993 = "so_do_1993"  # Giấy chứng nhận QSDĐ 1993 (bìa đỏ)
    SO_HONG_1995 = "so_hong_1995"  # Giấy chứng nhận QSH nhà ở (bìa hồng)
    UNIFIED_2009 = "unified_2009"  # GCN QSDĐ, QSH nhà ở và tài sản gắn liền (mẫu hợp nhất 2009)
    UNIFIED_2024 = "unified_2024"  # Mẫu thống nhất theo Luật Đất đai 2024
    UNKNOWN = "unknown"


class Certificate(Base, IDMixin, TimestampMixin):
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("organization.id", ondelete="CASCADE"), index=True
    )

    # File storage
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)

    # OCR
    ocr_engine: Mapped[str | None] = mapped_column(String(40))
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    ocr_raw_text: Mapped[str | None] = mapped_column(Text)
    ocr_completed_at = mapped_column(String(40))

    # Parsed fields (all PII — encrypted at column level via service layer)
    form: Mapped[CertificateForm] = mapped_column(
        Enum(CertificateForm, name="certificate_form"), default=CertificateForm.UNKNOWN
    )
    serial_number_enc: Mapped[str | None] = mapped_column(Text)  # Số seri (e.g., AB 123456)
    book_number_enc: Mapped[str | None] = mapped_column(Text)  # Số vào sổ cấp GCN
    issued_at: Mapped[str | None] = mapped_column(String(20))
    issued_by: Mapped[str | None] = mapped_column(String(200))  # UBND tỉnh/huyện/Sở TNMT
    owner_name_enc: Mapped[str | None] = mapped_column(Text)
    owner_id_enc: Mapped[str | None] = mapped_column(Text)  # CCCD/CMND
    parcel_number: Mapped[str | None] = mapped_column(String(40), index=True)  # Số thửa
    sheet_number: Mapped[str | None] = mapped_column(String(40), index=True)  # Số tờ bản đồ
    area_sqm: Mapped[float | None] = mapped_column(Numeric(14, 2))
    land_use_purpose: Mapped[str | None] = mapped_column(String(200))  # Mục đích sử dụng
    land_use_term: Mapped[str | None] = mapped_column(String(120))  # Thời hạn sử dụng
    address: Mapped[str | None] = mapped_column(String(500))
    ward: Mapped[str | None] = mapped_column(String(120))  # Xã/Phường
    district: Mapped[str | None] = mapped_column(String(120))  # Quận/Huyện
    province: Mapped[str | None] = mapped_column(String(120))  # Tỉnh/Thành

    extra: Mapped[dict | None] = mapped_column(JSON)

    organization: Mapped["Organization"] = relationship(back_populates="certificates")

    @staticmethod
    def new_id() -> str:
        return new_ulid("cert")
