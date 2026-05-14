# Sổ Đỏ Due Diligence Platform

> B2B platform for OCR, validation, and due diligence of Vietnamese land use right certificates ("Sổ Đỏ" / "Sổ Hồng"). Built for brokers, law firms, and bank collateral appraisal teams.

[![CI](https://github.com/your-org/sodo-dd/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/your-org/sodo-dd/actions)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

---

## What it does

1. **OCR Sổ Đỏ / Sổ Hồng** — extract structured data from scanned certificates (mẫu cũ 1993, mẫu 2009, mẫu hợp nhất 2024).
2. **Đối chiếu cổng dịch vụ công đất đai** — cross-check the extracted record against the National Land Information System (Hệ thống thông tin đất đai quốc gia) and provincial portals.
3. **Quy hoạch check** — overlay the parcel against zoning / land-use plans (quy hoạch sử dụng đất, quy hoạch xây dựng, kế hoạch sử dụng đất hằng năm).
4. **Lịch sử giao dịch** — pull historical transfers, mortgages, disputes, and pending changes flagged at the Land Registration Office (VPĐKĐĐ).
5. **Due diligence report** — produces a signed PDF + JSON report with risk score, red flags, and citation of every external source consulted.

## Who it's for

| Persona | Use case |
|---|---|
| **Môi giới BĐS** | Self-serve quick-check before listing or escrow. |
| **Luật sư / công chứng** | Pre-transaction legal review. |
| **Ngân hàng — Thẩm định TSBĐ** | Collateral asset due diligence at scale, with audit trail meeting SBV requirements. |

## Architecture

```
┌──────────────┐    ┌─────────────┐    ┌────────────────────┐
│ Next.js web  │───▶│  FastAPI    │───▶│ Postgres + S3      │
│ + B2B portal │    │  (REST API) │    └────────────────────┘
└──────────────┘    │             │    ┌────────────────────┐
┌──────────────┐    │             │───▶│ Celery workers     │
│ Partner APIs │───▶│             │    │  ▸ OCR (Tesseract  │
│ (HMAC)       │    │             │    │     + VietOCR)     │
└──────────────┘    │             │    │  ▸ Adapter calls   │
                    └─────────────┘    │  ▸ Report renderer │
                          │            └────────────────────┘
                          ▼
                ┌──────────────────────┐
                │ External adapters    │
                │ ▸ dichvucong.gov.vn  │
                │ ▸ VPĐKĐĐ provinces   │
                │ ▸ quyhoach.hanoi.vn  │
                │ ▸ TT BĐS giao dịch   │
                └──────────────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a deeper view.

## Quick start

```bash
# 1. Configure secrets
cp .env.example .env

# 2. Boot everything (api, worker, web, postgres, redis, minio)
make up

# 3. Apply migrations + seed demo org
make migrate
make seed

# 4. Open
open http://localhost:3000           # web portal
open http://localhost:8000/docs      # API (OpenAPI)
open http://localhost:9001           # MinIO console
```

Default seeded org has API key `sk_test_demo_xxxxx` — see `make seed` output.

## Repo layout

```
backend/      FastAPI service + Celery workers + Alembic
frontend/     Next.js 14 (App Router) B2B portal
infra/        nginx, prometheus, grafana, deployment manifests
docs/         Architecture, API, compliance, roadmap
samples/      Anonymised sample certificates for tests/demos
```

## API in 60 seconds

```bash
curl -X POST http://localhost:8000/api/v1/due-diligence/jobs \
  -H "Authorization: Bearer sk_test_demo_xxxxx" \
  -F "certificate=@samples/sample_so_do.jpg" \
  -F 'options={"include_zoning":true,"include_history":true}'

# → { "job_id": "ddj_01HXYZ...", "status": "queued" }

curl http://localhost:8000/api/v1/due-diligence/jobs/ddj_01HXYZ... \
  -H "Authorization: Bearer sk_test_demo_xxxxx"

# → { "status": "completed", "report_url": "...", "risk_score": 18, "red_flags": [...] }
```

Full API reference: [docs/API.md](docs/API.md).

## Compliance

- **Nghị định 13/2023/NĐ-CP** — personal data protection: all PII at rest is field-level encrypted (AES-GCM) with KMS-rotated keys; access produces immutable audit logs.
- **Luật Đất đai 2024** (effective 2024-08-01) — adapters track the unified certificate format and the consolidated `Giấy chứng nhận quyền sử dụng đất, quyền sở hữu tài sản gắn liền với đất`.
- **SBV Circular 41/2016/TT-NHNN** — for bank tenants, due-diligence reports include the appraisal-trail fields required for credit risk weighting.
- **External system access** — only via signed bilateral agreements (`MOU/`); no scraping in production.

## License

Proprietary. See [LICENSE](LICENSE).
