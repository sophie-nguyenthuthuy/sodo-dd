from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

from app.models.report import JobStatus, RiskLevel
from app.schemas.common import ORMModel


class DueDiligenceOptions(BaseModel):
    include_ocr: bool = True
    include_portal_verify: bool = True
    include_zoning: bool = True
    include_history: bool = True
    province_hint: str | None = None  # speed up portal/zoning routing
    parcel_hint: str | None = None  # if user already knows
    sheet_hint: str | None = None


class CreateJobRequest(BaseModel):
    """Used when uploading by reference (certificate already uploaded)."""

    certificate_id: str
    options: DueDiligenceOptions = Field(default_factory=DueDiligenceOptions)
    callback_url: HttpUrl | None = None


class RedFlag(BaseModel):
    code: str  # e.g. parcel_mismatch, planning_conflict, encumbrance
    severity: Literal["info", "warn", "high", "critical"]
    description: str
    source: str  # which adapter raised it


class ExternalSource(BaseModel):
    name: str  # e.g. "dichvucong.gov.vn — Tra cứu thông tin thửa đất"
    url: str | None = None
    queried_at: datetime
    response_hash: str  # sha256 of normalized response, for audit
    status: Literal["ok", "no_data", "error"]


class ReportSummary(ORMModel):
    id: str
    risk_score: int
    risk_level: RiskLevel
    red_flags: list[RedFlag]
    sources: list[ExternalSource]
    pdf_url: str | None = None


class JobOut(ORMModel):
    id: str
    status: JobStatus
    progress_pct: int
    options: dict[str, Any]
    certificate_id: str | None
    error_code: str | None
    error_detail: str | None
    started_at: datetime | None
    completed_at: datetime | None
    report: ReportSummary | None = None
    created_at: datetime
