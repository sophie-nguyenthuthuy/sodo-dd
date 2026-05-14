const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

async function call<T>(
  path: string,
  init: RequestInit & { token?: string } = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.token) headers.set('Authorization', `Bearer ${init.token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const r = await fetch(`${BASE}${path}`, { ...init, headers, cache: 'no-store' });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new ApiError(r.status, body?.error?.code ?? 'unknown', body?.error?.message ?? r.statusText);
  }
  return body as T;
}

export const api = {
  login: (email: string, password: string) =>
    call<{ access_token: string; expires_in: number }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  createApiKey: (token: string, name: string) =>
    call<{ id: string; key: string; key_prefix: string }>('/api/v1/auth/api-keys', {
      method: 'POST',
      token,
      body: JSON.stringify({ name }),
    }),
  submitJob: (apiKey: string, file: File, options: Record<string, unknown>) => {
    const fd = new FormData();
    fd.append('certificate', file);
    fd.append('options', JSON.stringify(options));
    return call<{ id: string; status: string }>('/api/v1/due-diligence/jobs', {
      method: 'POST',
      token: apiKey,
      body: fd,
    });
  },
  getJob: (apiKey: string, jobId: string) =>
    call<{
      id: string;
      status: string;
      progress_pct: number;
      report?: { risk_score: number; risk_level: string; red_flags: Array<{ code: string; severity: string; description: string }>; pdf_url?: string };
    }>(`/api/v1/due-diligence/jobs/${jobId}`, { token: apiKey }),
};
