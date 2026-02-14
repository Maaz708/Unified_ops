import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Unified Operations Platform",
  description: "Unified Ops SaaS"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}