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
  title: "돌파매매 전략(Breakout Strategy) - William O'Neil",
  description: "William O'Neil의 돌파매매 전략에 의한 미국 주식 신호 및 백테스트 결과",
  keywords: ["O'Neil", "Breakout", "Trading", "US Stocks", "CAN SLIM", "백테스트"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
