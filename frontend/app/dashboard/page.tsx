'use client';

import { useEffect, useRef, useState } from 'react';
import { api } from '@/lib/api';

type Job = Awaited<ReturnType<typeof api.getJob>>;

export default function Dashboard() {
  const [apiKey, setApiKey] = useState<string>('');
  const [jobs, setJobs] = useState<Record<string, Job>>({});
  const [submitting, setSubmitting] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('api_key');
    if (stored) setApiKey(stored);
  }, []);

  useEffect(() => {
    const ids = Object.keys(jobs).filter((id) => !['completed', 'failed', 'cancelled'].includes(jobs[id]!.status));
    if (!apiKey || ids.length === 0) return;
    const t = setInterval(async () => {
      for (const id of ids) {
        try {
          const j = await api.getJob(apiKey, id);
          setJobs((prev) => ({ ...prev, [id]: j }));
        } catch { /* ignore — polling */ }
      }
    }, 2500);
    return () => clearInterval(t);
  }, [apiKey, jobs]);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!inputRef.current?.files?.[0] || !apiKey) return;
    setSubmitting(true);
    try {
      const created = await api.submitJob(apiKey, inputRef.current.files[0], {
        include_zoning: true,
        include_history: true,
      });
      const full = await api.getJob(apiKey, created.id);
      setJobs((prev) => ({ ...prev, [created.id]: full }));
      inputRef.current.value = '';
    } finally {
      setSubmitting(false);
    }
  }

  function saveKey(k: string) {
    setApiKey(k);
    localStorage.setItem('api_key', k);
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Bảng điều khiển</h1>
        <div className="text-sm">
          <input
            placeholder="API key (sk_...)"
            className="rounded border border-zinc-300 px-3 py-1.5 text-sm w-72"
            value={apiKey}
            onChange={(e) => saveKey(e.target.value)}
          />
        </div>
      </header>

      <section className="mt-6 rounded-lg border bg-white p-5">
        <h2 className="font-semibold">Tải lên Sổ Đỏ để thẩm định</h2>
        <form onSubmit={onUpload} className="mt-3 flex items-center gap-3">
          <input ref={inputRef} type="file" accept="image/*,.pdf" className="text-sm" required />
          <button
            type="submit"
            disabled={submitting || !apiKey}
            className="rounded bg-brand-600 px-4 py-2 text-sm text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {submitting ? 'Đang gửi…' : 'Tạo job'}
          </button>
        </form>
      </section>

      <section className="mt-6">
        <h2 className="font-semibold">Jobs gần đây</h2>
        <div className="mt-3 space-y-3">
          {Object.values(jobs).length === 0 && (
            <p className="text-sm text-zinc-500">Chưa có job nào.</p>
          )}
          {Object.values(jobs).map((j) => (
            <JobCard key={j.id} job={j} />
          ))}
        </div>
      </section>
    </main>
  );
}

function JobCard({ job }: { job: Job }) {
  const level = job.report?.risk_level;
  const color =
    level === 'low' ? 'text-green-700'
    : level === 'medium' ? 'text-yellow-700'
    : level === 'high' ? 'text-orange-700'
    : level === 'critical' ? 'text-red-700'
    : 'text-zinc-600';
  return (
    <article className="rounded-lg border bg-white p-4">
      <div className="flex items-center justify-between">
        <code className="text-xs">{job.id}</code>
        <span className="text-xs uppercase text-zinc-500">{job.status}</span>
      </div>
      <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
        <div className="h-full bg-brand-500" style={{ width: `${job.progress_pct}%` }} />
      </div>
      {job.report && (
        <div className="mt-3 text-sm">
          <p>
            Điểm rủi ro: <b className={color}>{job.report.risk_score}</b> ({job.report.risk_level})
          </p>
          <ul className="mt-2 list-disc pl-5 text-xs">
            {job.report.red_flags.slice(0, 5).map((f, i) => (
              <li key={i}>
                <b>{f.severity}</b> — {f.code}: {f.description}
              </li>
            ))}
          </ul>
          {job.report.pdf_url && (
            <a className="mt-2 inline-block text-brand-600 underline" href={job.report.pdf_url}>
              Tải báo cáo PDF
            </a>
          )}
        </div>
      )}
    </article>
  );
}
