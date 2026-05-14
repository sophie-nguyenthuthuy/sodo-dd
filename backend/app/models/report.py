import enum
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IDMixin, TimestampMixin, new_ulid


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    OCR = "ocr"
    VERIFYING = "verifying"
    ZONING = "zoning"
    HISTORY = "history"
    SCORING = "scoring"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, enum.Enum):
    LOW = "low"          # 0-29
    MEDIUM = "medium"    # 30-59
    HIGH = "high"        # 60-79
    CRITICAL = "critical"  # 80-100


class DueDiligenceJob(Base, IDMixin, TimestampMixin):
    organization_id: Mapped[str] = mapped_column(ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    certificate_id: Mapped[str | None] = mapped_column(ForeignKey("certificate.id", ondelete="SET NULL"))
    api_key_id: Mapped[str | None] = mapped_column(ForeignKey("api_key.id", ondelete="SET NULL"))

    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.QUEUED, index=True
    )
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_detail: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    callback_url: Mapped[str | None] = mapped_column(String(500))

    report: Mapped["DueDiligenceReport | None"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )

    @staticmethod
    def new_id() -> str:
        return new_ulid("ddj")


class DueDiligenceReport(Base, IDMixin, TimestampMixin):
    job_id: Mapped[str] = mapped_column(ForeignKey("due_diligence_job.id", ondelete="CASCADE"), unique=True)

    risk_score: Mapped[int] = mapped_column(Integer, default=0)         # 0-100
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, name="risk_level"))
    red_flags: Mapped[list] = mapped_column(JSON, default=list)         # [{code, severity, description, source}]
    findings: Mapped[dict] = mapped_column(JSON, default=dict)          # full structured findings
    sources: Mapped[list] = mapped_column(JSON, default=list)           # external sources consulted
    pdf_key: Mapped[str | None] = mapped_column(String(500))            # S3 key for signed PDF
    pdf_sha256: Mapped[str | None] = mapped_column(String(64))

    job: Mapped["DueDiligenceJob"] = relationship(back_populates="report")

    @staticmethod
    def new_id() -> str:
        return new_ulid("ddr")
