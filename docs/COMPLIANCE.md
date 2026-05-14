# Compliance posture

## Vietnamese regulation

| Regulation | Applies because | Implementation |
|---|---|---|
| **Luật Đất đai 2024** (eff. 2024-08-01) | Source-of-truth for parcel data and unified GCN form | Adapters track the consolidated certificate form `unified_2024`; parser handles legacy 1993/1995/2009 forms for back-catalog uploads. |
| **Nghị định 13/2023/NĐ-CP** (PDPL) | We store CCCD, owner names, contact info | Field-level AES-GCM (256) for PII columns; access logged in `audit_log`; data subject rights endpoints planned (see ROADMAP). |
| **Luật Giao dịch điện tử 2023** | Reports must be tamper-evident | Each generated PDF stores SHA-256 in DB + sources include `response_hash` of each external lookup. |
| **SBV TT 41/2016/TT-NHNN** | Bank tenants use reports for credit risk weighting | Report PDF contains audit trail required by appraisal teams (sources, timestamps, hash digests). |
| **Quy chế chia sẻ dữ liệu đất đai** (Bộ TNMT) | Land portal API access | Live mode requires bilateral MOU; no scraping. `LAND_PORTAL_MODE=live` requires `LAND_PORTAL_API_KEY`. |

## Operational controls

1. **Encryption** — TLS 1.2+ in transit (enforced at nginx); AES-GCM 256 at rest for PII.
2. **Access control** — RBAC (owner/admin/analyst/viewer) + scoped API keys.
3. **Audit log** — append-only, indexed by `(action, resource_type, resource_id)`.
4. **Data residency** — production deployments must use VN-region object storage.
5. **Retention** — originals retained 7 years (TT 41), reports 10 years; deletion is
   logical until retention expiry, then cryptographic shred via key rotation.
6. **Incident response** — Sentry alerts feed PagerDuty rotation; security incidents
   reportable to NCSC under NĐ 13/2023 within 72h.

## Threats handled

| Threat | Mitigation |
|---|---|
| API key theft | Stored as HMAC; rotation via dashboard; per-key rate limiting. |
| Replay of webhook payload | HMAC-with-timestamp + 5-min skew window. |
| Tampered report | PDF SHA-256 stored; recipients verify before legal use. |
| Mass scraping of partner systems | Single circuit-breaker per adapter; live mode requires MOU credentials. |
| Inference attack on PII via logs | Logging redacts `*_enc` fields and CCCD patterns at the formatter level. |
