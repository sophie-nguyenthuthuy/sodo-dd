from datetime import datetime

from pydantic import BaseModel, Field

from app.models.certificate import CertificateForm
from app.schemas.common import ORMModel


class CertificateParsed(BaseModel):
    """Parsed (decrypted) view — only returned to authorized callers."""

    form: CertificateForm
    serial_number: str | None = None
    book_number: str | None = None
    issued_at: str | None = None
    issued_by: str | None = None
    owner_name: str | None = None
    owner_id: str | None = None
    parcel_number: str | None = None
    sheet_number: str | None = None
    area_sqm: float | None = None
    land_use_purpose: str | None = None
    land_use_term: str | None = None
    address: str | None = None
    ward: str | None = None
    district: str | None = None
    province: str | None = None


class CertificateOut(ORMModel):
    id: str
    file_sha256: str
    file_size: int
    mime_type: str
    ocr_engine: str | None
    ocr_confidence: float | None
    form: CertificateForm
    created_at: datetime
    parsed: CertificateParsed | None = Field(default=None)
