import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "잇뉴 | 통합 분석 플랫폼",
  description: "고객과 품목 데이터를 한눈에 분석하는 잇뉴 대시보드",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
