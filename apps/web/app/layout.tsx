import type { Metadata } from "next";
import Link from "next/link";
import { SiteHeader } from "@/components/SiteHeader";
import { MemberSessionProvider } from "@/components/MemberSession";
import { noIndex, siteDescription, siteURL } from "@/lib/seo";
import "./globals.css";
export const dynamic = "force-dynamic";
export function generateMetadata(): Metadata { return {
  metadataBase: siteURL(),
  title: { default: "Artline — Art, literature & history", template: "%s — Artline" },
  description: siteDescription,
  robots: noIndex,
  verification: { google: process.env.ARTLINE_GOOGLE_SITE_VERIFICATION || undefined, other: process.env.ARTLINE_BING_SITE_VERIFICATION ? { "msvalidate.01": process.env.ARTLINE_BING_SITE_VERIFICATION } : undefined },
}; }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <MemberSessionProvider>
    <SiteHeader />
    {children}
    <footer className="site-footer"><p>Artline. Art, literature and history in context.</p><nav aria-label="More"><Link href="/art-history-timeline">Art history guide</Link><Link href="/artists">Artist directory</Link><Link href="/museums">Museums</Link><Link href="/about">About & sources</Link><Link href="/privacy">Privacy</Link></nav></footer>
    </MemberSessionProvider>
  </body></html>;
}
