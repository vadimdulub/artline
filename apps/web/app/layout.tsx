import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { researchPreviewEnabled } from "@/lib/server-api";
import "./globals.css";
export const dynamic = "force-dynamic";
export const metadata: Metadata = {
  title: { default: "Artline — Atlas of painters", template: "%s — Artline" },
  description: "Explore painters, their overlapping lives, and their works from 1100 to 2000.",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <SiteHeader preview={researchPreviewEnabled()} />
    {children}
    <footer className="site-footer"><p>Artline. A continuing study of painting.</p><nav aria-label="More"><Link href="/coverage">Coverage</Link><Link href="/imports">Imports</Link><Link href="/about">About & sources</Link></nav></footer>
  </body></html>;
}
