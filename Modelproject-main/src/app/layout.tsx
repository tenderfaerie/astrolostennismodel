import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AstroTennis",
  description: "Live tennis, historical analytics, and prop projections"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
