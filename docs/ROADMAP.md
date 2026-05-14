# Roadmap

## Phase 1 — MVP (this scaffold)

- [x] Multi-tenant org + API key + JWT auth
- [x] Upload certificate, queued OCR via Celery
- [x] Mock adapters for portal / zoning / history
- [x] Risk scoring v1 + signed PDF report
- [x] Webhook delivery with HMAC signing
- [x] CI: lint, test, build, CodeQL, Trivy, gitleaks

## Phase 2 — Pilot

- [ ] VietOCR engine for handwritten fields (owner name, address)
- [ ] Live `LandPortalAdapter` per first two pilot provinces (Hà Nội, HCMC)
- [ ] Bulk job endpoint + zip ingest for bank tenants
- [ ] Web dashboard: search by parcel, export CSV, RBAC management UI
- [ ] Two-person review workflow for `risk_level >= high` jobs

## Phase 3 — Scale

- [ ] OpenTelemetry tracing across api → worker → adapter
- [ ] Multi-region (VN-North / VN-South) active-active
- [ ] Mobile app for field photo capture with on-device pre-OCR
- [ ] Public data subject rights endpoint (NĐ 13/2023 art. 14)
- [ ] Risk model: ML-trained calibration on retro corpus
- [ ] Optional blockchain anchor of report hashes for non-repudiation

## Open questions

- Should encumbrance data be cached and re-validated on read, or always re-queried?
  Banks prefer fresh; brokers tolerate 24h staleness — likely a per-tenant policy.
- VietOCR vs Cloud Vision: VietOCR for handwriting accuracy, Vision for layout / table
  extraction. Decision: VietOCR for owner block, Vision for the parcel table.
