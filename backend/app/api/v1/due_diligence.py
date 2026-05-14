import hashlib
import json

from fastapi import APIRouter, File, Form, UploadFile, status

from app.api.deps import ApiKeyDep, SessionDep
from app.core.exceptions import BadRequest, NotFound
from app.models import Certificate, DueDiligenceJob
from app.models.certificate import CertificateForm
from app.models.report import JobStatus
from app.schemas.due_diligence import (
    CreateJobRequest,
    DueDiligenceOptions,
    JobOut,
    ReportSummary,
)
from app.services.storage import presigned_get, upload_bytes
from app.workers.tasks import run_due_diligence

router = APIRouter(prefix="/due-diligence", tags=["due-diligence"])


def _job_to_out(job: DueDiligenceJob) -> JobOut:
    report = None
    if job.report is not None:
        pdf_url = presigned_get(job.report.pdf_key, expires=3600) if job.report.pdf_key else None
        report = ReportSummary(
            id=job.report.id,
            risk_score=job.report.risk_score,
            risk_level=job.report.risk_level,
            red_flags=job.report.red_flags,
            sources=job.report.sources,
            pdf_url=pdf_url,
        )
    return JobOut(
        id=job.id,
        status=job.status,
        progress_pct=job.progress_pct,
        options=job.options,
        certificate_id=job.certificate_id,
        error_code=job.error_code,
        error_detail=job.error_detail,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        report=report,
    )


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
async def create_job_inline(
    db: SessionDep,
    ak: ApiKeyDep,
    certificate: UploadFile = File(..., description="Sổ Đỏ image or PDF"),
    options: str | None = Form(default=None, description="JSON-encoded DueDiligenceOptions"),
    callback_url: str | None = Form(default=None),
) -> JobOut:
    body = await certificate.read()
    if not body:
        raise BadRequest("empty file")
    sha = hashlib.sha256(body).hexdigest()
    key = f"certificates/{ak.organization_id}/{sha[:2]}/{sha}"
    upload_bytes(key, body, content_type=certificate.content_type or "application/octet-stream")

    cert = Certificate(
        id=Certificate.new_id(),
        organization_id=ak.organization_id,
        file_key=key,
        file_sha256=sha,
        file_size=len(body),
        mime_type=certificate.content_type or "application/octet-stream",
        form=CertificateForm.UNKNOWN,
    )
    db.add(cert)

    try:
        opts = DueDiligenceOptions(**json.loads(options)) if options else DueDiligenceOptions()
    except (json.JSONDecodeError, ValueError) as exc:
        raise BadRequest(f"invalid options JSON: {exc}") from exc

    job = DueDiligenceJob(
        id=DueDiligenceJob.new_id(),
        organization_id=ak.organization_id,
        api_key_id=ak.id,
        certificate_id=cert.id,
        status=JobStatus.QUEUED,
        options=opts.model_dump(),
        callback_url=callback_url,
    )
    db.add(job)
    db.commit()

    run_due_diligence.delay(job.id)
    return _job_to_out(job)


@router.post("/jobs/by-reference", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def create_job_by_reference(req: CreateJobRequest, db: SessionDep, ak: ApiKeyDep) -> JobOut:
    cert = db.get(Certificate, req.certificate_id)
    if cert is None or cert.organization_id != ak.organization_id:
        raise NotFound("certificate not found")

    job = DueDiligenceJob(
        id=DueDiligenceJob.new_id(),
        organization_id=ak.organization_id,
        api_key_id=ak.id,
        certificate_id=cert.id,
        status=JobStatus.QUEUED,
        options=req.options.model_dump(),
        callback_url=str(req.callback_url) if req.callback_url else None,
    )
    db.add(job)
    db.commit()
    run_due_diligence.delay(job.id)
    return _job_to_out(job)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: SessionDep, ak: ApiKeyDep) -> JobOut:
    job = db.get(DueDiligenceJob, job_id)
    if job is None or job.organization_id != ak.organization_id:
        raise NotFound("job not found")
    return _job_to_out(job)
