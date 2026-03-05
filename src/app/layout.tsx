import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MorgenAI — AI 엔지니어를 위한 큐레이션 뉴스",
  description:
    "매일 업데이트되는 AI 뉴스, 논문, 노하우, 사용사례를 한국어로 큐레이션합니다.",
  openGraph: {
    title: "MorgenAI",
    description: "AI 엔지니어를 위한 큐레이션 뉴스",
    type: "website",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "MorgenAI",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko" className="dark" suppressHydrationWarning>
      <head>
        <meta name="theme-color" content="#121018" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="#f5f0eb" media="(prefers-color-scheme: light)" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
      </body>
    </html>
  );
}
