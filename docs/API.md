# API reference (v1)

Base URL: `https://api.sodo-dd.vn`  ·  All endpoints accept and return JSON unless stated.

## Authentication

Two auth flows:

1. **API keys** (B2B integrations) — `Authorization: Bearer sk_live_<random>`
2. **JWT** (web portal) — `Authorization: Bearer <jwt>` issued by `POST /auth/login`

API keys are rate-limited via a token bucket: 60 rpm sustained, burst 20, configurable per
key. Repeated 429s should be retried with exponential backoff respecting `Retry-After`.

## Errors

All errors:

```json
{ "error": { "code": "rate_limited", "message": "API key rate limit exceeded" } }
```

| code | http | meaning |
|---|---|---|
| `unauthorized` | 401 | missing / invalid token |
| `forbidden` | 403 | scope or role insufficient |
| `not_found` | 404 | resource missing or not owned by org |
| `bad_request` | 400 | validation failed |
| `rate_limited` | 429 | back off |
| `upstream_unavailable` | 502 | external partner system error |

## Endpoints

### `POST /api/v1/auth/login`

Body: `{ "email": "...", "password": "..." }`

Returns `{ "access_token": "...", "expires_in": 1800 }`.

### `POST /api/v1/auth/api-keys`

Owner / admin only. Body: `{ "name": "production-ingest", "scopes": ["due_diligence:write"] }`

Returns the raw key **once** — never retrievable again.

### `POST /api/v1/certificates`

multipart/form-data, field `file=<image|pdf>`. Returns the created `Certificate`. Mime
must be one of `image/jpeg | image/png | image/tiff | application/pdf`. Max 25 MB.

### `POST /api/v1/due-diligence/jobs`

multipart/form-data; uploads + triggers in one shot.

| field | type | notes |
|---|---|---|
| `certificate` | file | required |
| `options` | string | optional JSON-encoded `DueDiligenceOptions` |
| `callback_url` | string | optional, webhook will also fire if registered |

Returns the `Job` with status `queued`.

`DueDiligenceOptions`:

```json
{
  "include_ocr": true,
  "include_portal_verify": true,
  "include_zoning": true,
  "include_history": true,
  "province_hint": "Hà Nội",
  "parcel_hint": "142",
  "sheet_hint": "27"
}
```

### `POST /api/v1/due-diligence/jobs/by-reference`

JSON body. Use when the certificate has already been uploaded.

```json
{ "certificate_id": "cert_01HX...", "options": { "include_zoning": false } }
```

### `GET /api/v1/due-diligence/jobs/{job_id}`

```json
{
  "id": "ddj_01HX...",
  "status": "completed",
  "progress_pct": 100,
  "certificate_id": "cert_01HX...",
  "created_at": "2026-05-14T03:11:00Z",
  "completed_at": "2026-05-14T03:11:42Z",
  "report": {
    "id": "ddr_01HX...",
    "risk_score": 18,
    "risk_level": "low",
    "red_flags": [],
    "sources": [
      { "name": "land_portal", "status": "ok", "queried_at": "...",
        "response_hash": "8f3..." }
    ],
    "pdf_url": "https://...presigned..."
  }
}
```

## Webhooks

`POST /api/v1/webhooks` registers an endpoint. The platform delivers events with:

- `Content-Type: application/json`
- `X-Sodo-Event: dd.completed | dd.failed`
- `X-Sodo-Signature: t=<unix>,v1=<hex_hmac_sha256(secret, "<t>." + body)>`

Verify with the helper in `app/core/security.py::verify_webhook` or your own
constant-time HMAC. Allow a clock skew of ±5 minutes.

Delivery is retried with exponential backoff up to 4 attempts; permanently failed
deliveries are surfaced in the dashboard.
