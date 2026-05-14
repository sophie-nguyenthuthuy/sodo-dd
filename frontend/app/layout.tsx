import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sổ Đỏ Due Diligence',
  description: 'OCR + đối chiếu + quy hoạch + lịch sử giao dịch cho môi giới, luật sư, ngân hàng',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
