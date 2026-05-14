import Link from 'next/link';

export default function Landing() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-block h-8 w-8 rounded bg-brand-600" />
          <span className="text-lg font-semibold">Sổ Đỏ DD</span>
        </div>
        <Link href="/login" className="text-sm text-brand-600 hover:underline">
          Đăng nhập →
        </Link>
      </header>

      <section className="mt-16 max-w-3xl">
        <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
          Thẩm định Sổ Đỏ tự động — nhanh, an toàn, có dấu vết kiểm toán.
        </h1>
        <p className="mt-5 text-lg text-zinc-600">
          OCR Sổ Đỏ / Sổ Hồng, đối chiếu Cổng dịch vụ công đất đai, kiểm tra quy hoạch và lịch sử
          giao dịch — trong một báo cáo PDF có chữ ký số. Dành cho môi giới BĐS, luật sư, công
          chứng, và bộ phận thẩm định tài sản đảm bảo của ngân hàng.
        </p>

        <div className="mt-8 flex gap-3">
          <Link
            href="/login"
            className="rounded bg-brand-600 px-5 py-3 text-white shadow hover:bg-brand-700"
          >
            Bắt đầu miễn phí
          </Link>
          <a
            href="http://localhost:8000/docs"
            className="rounded border border-zinc-300 px-5 py-3 text-zinc-700 hover:bg-zinc-100"
          >
            Xem API docs
          </a>
        </div>
      </section>

      <section className="mt-20 grid gap-6 md:grid-cols-3">
        {FEATURES.map((f) => (
          <article key={f.title} className="rounded-lg border border-zinc-200 bg-white p-5">
            <h3 className="font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-zinc-600">{f.desc}</p>
          </article>
        ))}
      </section>

      <section className="mt-20">
        <h2 className="text-xl font-semibold">Phù hợp cho</h2>
        <ul className="mt-4 grid gap-3 text-sm md:grid-cols-3">
          <li className="rounded border border-zinc-200 bg-white p-4">
            <b>Môi giới BĐS</b> — pre-check trước niêm yết, escrow.
          </li>
          <li className="rounded border border-zinc-200 bg-white p-4">
            <b>Luật sư / Công chứng</b> — rà soát pháp lý trước giao dịch.
          </li>
          <li className="rounded border border-zinc-200 bg-white p-4">
            <b>Ngân hàng — Thẩm định TSBĐ</b> — đối chiếu hàng loạt, đầy đủ dấu vết SBV.
          </li>
        </ul>
      </section>

      <footer className="mt-24 border-t pt-6 text-xs text-zinc-500">
        © 2026 Sổ Đỏ DD Platform · Tuân thủ NĐ 13/2023/NĐ-CP, Luật Đất đai 2024, TT 41/2016/TT-NHNN.
      </footer>
    </main>
  );
}

const FEATURES = [
  {
    title: 'OCR đa mẫu',
    desc: 'Trích xuất trường có cấu trúc từ mẫu Sổ Đỏ 1993, Sổ Hồng 1995, mẫu hợp nhất 2009/2024.',
  },
  {
    title: 'Đối chiếu Cổng dịch vụ công',
    desc: 'So khớp với hệ thống thông tin đất đai quốc gia và VPĐKĐĐ tỉnh/thành.',
  },
  {
    title: 'Quy hoạch & lịch sử',
    desc: 'Phát hiện xung đột quy hoạch, thế chấp, tranh chấp, thay đổi đang chờ xử lý.',
  },
];
