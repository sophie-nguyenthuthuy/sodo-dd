# Architecture

## Components

| Component | Tech | Responsibility |
|---|---|---|
| `api` | FastAPI + Uvicorn | Synchronous HTTP surface, auth, request validation, job creation, presigned download. |
| `worker` | Celery (Redis broker) | Long-running OCR + adapter pipeline, PDF rendering, webhook delivery. |
| `beat` | Celery beat | Periodic housekeeping (stale-job purge, retention sweep). |
| `web` | Next.js 14 (App Router) | B2B portal: upload, job tracking, key management. |
| `postgres` | Postgres 16 | System of record for orgs, certificates, jobs, reports, audit log. |
| `redis` | Redis 7 | Queue, rate limit, locks. |
| `minio` / `s3` | S3-compatible | Originals (Sổ Đỏ scans) + generated PDF reports. |

## Pipeline

```
upload  ─►  api    ─►  Job.queued
                       │
                       ▼
                    worker.run_due_diligence
                       │
                       ├── OCR   (Tesseract / VietOCR / Vision)
                       ├── parse → ParsedCertificate
                       ├── adapters (concurrently)
                       │     ├── land_portal      (dichvucong.gov.vn / national land DB)
                       │     ├── zoning          (province quy hoạch APIs)
                       │     └── transaction_history (VPĐKĐĐ tỉnh)
                       ├── score → (risk_score, risk_level, red_flags)
                       ├── render PDF (reportlab)
                       ├── upload PDF to S3
                       └── emit webhook (HMAC-signed)
```

## Data flow & sensitive fields

PII columns end with `_enc` and are AES-GCM (256-bit) at the column level using a key
referenced by `FIELD_ENCRYPTION_KEY_ID`. Production rotates this key via AWS KMS / cloud
HSM. Decryption is only performed inside the API process when the caller's API key has
the `due_diligence:read` scope and the audit log records the access.

## Adapters

Every external integration implements `BaseAdapter` and supports `mode=mock | live`. The
mock implementation simulates the contracts seen in the field so the entire pipeline
boots without live partner credentials. The live implementation is wrapped in a
`tenacity` retry chain with exponential backoff.

## Observability

- Structured JSON logs to stdout (`structlog`), shipped to Loki / CloudWatch.
- Prometheus metrics at `/metrics`, scraped by `infra/prometheus`.
- Optional Sentry via `SENTRY_DSN`.
- OpenTelemetry endpoint via `OTEL_EXPORTER_OTLP_ENDPOINT` (uncomment auto-instrumentation
  in `main.py` when activated).

## Deployment topology (production sketch)

- **Edge**: Cloudflare / VPC ingress → nginx → api/web.
- **API**: 3+ pods (`uvicorn --workers 4`), HPA on RPS.
- **Workers**: separate pool with higher CPU; OCR pinned to GPU-enabled nodes when
  VietOCR is enabled.
- **DB**: managed Postgres with PITR, read replica for analytics.
- **Storage**: S3 with object-lock for reports (compliance hold).
- **Secrets**: AWS Secrets Manager / GCP Secret Manager. Never .env in prod.
