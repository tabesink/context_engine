import type { Metadata } from "next";
import localFont from "next/font/local";
import { Providers } from "@/app/providers";
import "./globals.css";

const geistSans = localFont({
  variable: "--font-geist-sans",
  src: [
    { path: "./fonts/geist-latin.woff2", weight: "100 900", style: "normal" },
    { path: "./fonts/geist-latin-ext.woff2", weight: "100 900", style: "normal" },
  ],
  display: "swap",
});

const geistMono = localFont({
  variable: "--font-geist-mono",
  src: [
    { path: "./fonts/geist-mono-latin.woff2", weight: "100 900", style: "normal" },
    { path: "./fonts/geist-mono-latin-ext.woff2", weight: "100 900", style: "normal" },
  ],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Knowledge Graph",
  description: "Lean local chat client for query servers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} min-h-screen bg-background text-foreground`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
