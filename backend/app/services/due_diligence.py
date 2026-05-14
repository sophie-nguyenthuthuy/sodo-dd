"""Due-diligence orchestration: OCR → portal verify → zoning → history → score → render."""
from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import encrypt_field
from app.logging import get_logger
from app.models import Certificate, DueDiligenceJob, DueDiligenceReport, Organization
from app.models.report import JobStatus
from app.services.adapters import (
    LandPortalAdapter,
    TransactionHistoryAdapter,
    ZoningAdapter,
)
from app.services.adapters.base import AdapterResponse
from app.services.ocr.base import get_engine
from app.services.ocr.parser import CertificateParser, ParsedCertificate
from app.services.report_generator import render as render_pdf
from app.services.scoring import score as compute_score
from app.services.storage import download_bytes, upload_bytes

log = get_logger("dd")


def _adapter_response_to_source(r: AdapterResponse) -> dict[str, Any]:
    return {
        "name": r.name,
        "url": r.url,
        "status": r.status,
        "queried_at": r.queried_at.isoformat(),
        "response_hash": r.response_hash,
        "error": r.error,
    }


def _adapter_response_to_payload(r: AdapterResponse) -> dict[str, Any]:
    return {"status": r.status, "payload": r.payload, "error": r.error}


def _save_parsed_to_certificate(cert: Certificate, parsed: ParsedCertificate) -> None:
    cert.form = parsed.form
    cert.serial_number_enc = encrypt_field(parsed.serial_number)
    cert.book_number_enc = encrypt_field(parsed.book_number)
    cert.owner_name_enc = encrypt_field(parsed.owner_name)
    cert.owner_id_enc = encrypt_field(parsed.owner_id)
    cert.parcel_number = parsed.parcel_number
    cert.sheet_number = parsed.sheet_number
    cert.area_sqm = parsed.area_sqm
    cert.issued_at = parsed.issued_at
    cert.issued_by = parsed.issued_by
    cert.land_use_purpose = parsed.land_use_purpose
    cert.land_use_term = parsed.land_use_term
    cert.address = parsed.address
    cert.ward = parsed.ward
    cert.district = parsed.district
    cert.province = parsed.province
    cert.extra = {"field_confidence": parsed.field_confidence}


def process_job(db: Session, job: DueDiligenceJob) -> DueDiligenceReport:
    if job.certificate_id is None:
        raise ValueError("job has no certificate_id")
    cert = db.get(Certificate, job.certificate_id)
    org = db.get(Organization, job.organization_id)
    if cert is None or org is None:
        raise ValueError("certificate or organization missing")

    options: dict[str, Any] = job.options or {}
    job.status = JobStatus.OCR
    job.started_at = datetime.now(UTC)
    job.progress_pct = 5
    db.commit()

    # ─── OCR
    blob = download_bytes(cert.file_key)
    engine = get_engine(settings.ocr_engine)
    ocr = engine.extract(blob, mime_type=cert.mime_type)
    cert.ocr_engine = ocr.engine
    cert.ocr_confidence = ocr.confidence
    cert.ocr_raw_text = ocr.text
    cert.ocr_completed_at = datetime.now(UTC).isoformat()

    parsed = CertificateParser().parse(ocr.text)
    _save_parsed_to_certificate(cert, parsed)
    db.commit()
    job.progress_pct = 30
    db.commit()

    parsed_dict = asdict(parsed)
    parsed_dict["form"] = parsed.form.value

    portal_result: AdapterResponse | None = None
    zoning_result: AdapterResponse | None = None
    history_result: AdapterResponse | None = None

    # ─── Portal verify
    if options.get("include_portal_verify", True):
        job.status = JobStatus.VERIFYING
        db.commit()
        portal = LandPortalAdapter(
            mode=settings.land_portal_mode,
            api_key=settings.land_portal_api_key or None,
        )
        portal_result = portal.query(
            serial_number=parsed.serial_number,
            book_number=parsed.book_number,
            parcel_number=parsed.parcel_number,
            sheet_number=parsed.sheet_number,
            owner_name=parsed.owner_name,
            area_sqm=parsed.area_sqm,
            province=parsed.province or options.get("province_hint"),
        )
        job.progress_pct = 50
        db.commit()

    # ─── Zoning
    if options.get("include_zoning", True):
        job.status = JobStatus.ZONING
        db.commit()
        zoning = ZoningAdapter(mode=settings.zoning_provider)
        zoning_result = zoning.query(
            parcel_number=parsed.parcel_number or options.get("parcel_hint"),
            sheet_number=parsed.sheet_number or options.get("sheet_hint"),
            province=parsed.province or options.get("province_hint"),
            land_use_purpose=parsed.land_use_purpose,
        )
        job.progress_pct = 70
        db.commit()

    # ─── Transaction history
    if options.get("include_history", True):
        job.status = JobStatus.HISTORY
        db.commit()
        history = TransactionHistoryAdapter(mode=settings.transaction_history_provider)
        history_result = history.query(
            serial_number=parsed.serial_number,
            parcel_number=parsed.parcel_number,
            sheet_number=parsed.sheet_number,
            province=parsed.province or options.get("province_hint"),
        )
        job.progress_pct = 85
        db.commit()

    # ─── Score
    job.status = JobStatus.SCORING
    db.commit()
    risk_score, risk_level, red_flags = compute_score(
        parsed=parsed_dict,
        ocr_confidence=ocr.confidence,
        portal=_adapter_response_to_payload(portal_result) if portal_result else None,
        zoning=_adapter_response_to_payload(zoning_result) if zoning_result else None,
        history=_adapter_response_to_payload(history_result) if history_result else None,
    )

    sources = [
        _adapter_response_to_source(r)
        for r in (portal_result, zoning_result, history_result)
        if r is not None
    ]

    # ─── Render PDF
    job.status = JobStatus.RENDERING
    db.commit()
    pdf_bytes, pdf_sha = render_pdf(
        job_id=job.id,
        organization_name=org.name,
        parsed=parsed_dict,
        risk_score=risk_score,
        risk_level=risk_level.value,
        red_flags=red_flags,
        sources=sources,
    )
    pdf_key = f"reports/{org.id}/{job.id}.pdf"
    upload_bytes(pdf_key, pdf_bytes, content_type="application/pdf")

    report = DueDiligenceReport(
        id=DueDiligenceReport.new_id(),
        job_id=job.id,
        risk_score=risk_score,
        risk_level=risk_level,
        red_flags=red_flags,
        findings={
            "parsed": parsed_dict,
            "ocr_confidence": ocr.confidence,
            "portal": portal_result.payload if portal_result else None,
            "zoning": zoning_result.payload if zoning_result else None,
            "history": history_result.payload if history_result else None,
        },
        sources=sources,
        pdf_key=pdf_key,
        pdf_sha256=pdf_sha,
    )
    db.add(report)

    job.status = JobStatus.COMPLETED
    job.progress_pct = 100
    job.completed_at = datetime.now(UTC)
    db.commit()
    log.info("dd.completed", job_id=job.id, risk_score=risk_score, risk_level=risk_level.value)
    return report
