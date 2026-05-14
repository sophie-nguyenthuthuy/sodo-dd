from datetime import UTC, datetime, timedelta

from celery.utils.log import get_task_logger

from app.database import session_scope
from app.models import DueDiligenceJob, WebhookEndpoint
from app.models.report import JobStatus
from app.services.due_diligence import process_job
from app.workers.celery_app import celery_app
from app.workers.webhooks import deliver_event

log = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.run_due_diligence",
    autoretry_for=(Exception,),
    max_retries=2,
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
)
def run_due_diligence(self, job_id: str) -> str:
    log.info("dd start job_id=%s", job_id)
    with session_scope() as db:
        job = db.get(DueDiligenceJob, job_id)
        if job is None:
            log.warning("job not found: %s", job_id)
            return "missing"
        try:
            process_job(db, job)
        except Exception as exc:
            log.exception("dd failed job_id=%s", job_id)
            job.status = JobStatus.FAILED
            job.error_code = type(exc).__name__
            job.error_detail = str(exc)[:2000]
            job.completed_at = datetime.now(UTC)
            db.commit()

            for wh in db.query(WebhookEndpoint).filter_by(
                organization_id=job.organization_id, is_active=True
            ):
                if "dd.failed" in wh.events:
                    deliver_event(wh, "dd.failed", {"job_id": job.id, "error": job.error_code})
            raise

        for wh in db.query(WebhookEndpoint).filter_by(
            organization_id=job.organization_id, is_active=True
        ):
            if "dd.completed" in wh.events:
                deliver_event(
                    wh,
                    "dd.completed",
                    {
                        "job_id": job.id,
                        "risk_score": job.report.risk_score if job.report else None,
                        "risk_level": job.report.risk_level.value if job.report else None,
                    },
                )
    return "ok"


@celery_app.task(name="app.workers.tasks.purge_stale_jobs")
def purge_stale_jobs() -> int:
    """Mark jobs as failed if stuck >30 min."""
    cutoff = datetime.now(UTC) - timedelta(minutes=30)
    with session_scope() as db:
        rows = (
            db.query(DueDiligenceJob)
            .filter(DueDiligenceJob.completed_at.is_(None))
            .filter(DueDiligenceJob.started_at < cutoff)
            .all()
        )
        for row in rows:
            row.status = JobStatus.FAILED
            row.error_code = "timeout"
            row.error_detail = "Job exceeded 30 minute SLA"
            row.completed_at = datetime.now(UTC)
        return len(rows)
