import type { Metadata } from "next";
import Script from "next/script";
import Link from "@/components/MemberLink";
import { BookmarkProvider } from "@/components/Bookmarks";
import "@/components/Bookmarks.css";
import { SiteHeader } from "@/components/SiteHeader";
import { MemberAccessProvider } from "@/components/MemberLink";
import "./account/account.css";
import { MemberSessionProvider } from "@/components/MemberSession";
import { noIndex, siteDescription, siteURL } from "@/lib/seo";
import { cloudflareWebAnalyticsToken } from "@/lib/web-analytics";
import "./globals.css";
import "./mobile.css";
export const dynamic = "force-dynamic";
export function generateMetadata(): Metadata { return {
  metadataBase: siteURL(),
  title: { default: "Artline — Art, literature & history", template: "%s — Artline" },
  description: siteDescription,
  robots: noIndex,
  verification: { google: process.env.ARTLINE_GOOGLE_SITE_VERIFICATION || undefined, other: process.env.ARTLINE_BING_SITE_VERIFICATION ? { "msvalidate.01": process.env.ARTLINE_BING_SITE_VERIFICATION } : undefined },
}; }
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const analyticsToken = cloudflareWebAnalyticsToken();
  return <html lang="en"><body>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <MemberSessionProvider><MemberAccessProvider><BookmarkProvider>
    <SiteHeader />
    {children}
    <footer className="site-footer"><p>Artline. Art, literature and history in context.</p><nav aria-label="More"><Link href="/guides">Guides</Link><Link href="/artists">Artist directory</Link><Link href="/museums">Museums</Link><Link href="/about">About</Link><Link href="/privacy">Privacy</Link></nav></footer>
    </BookmarkProvider></MemberAccessProvider></MemberSessionProvider>
    {analyticsToken && <Script
      id="cloudflare-web-analytics"
      type="module"
      src="https://static.cloudflareinsights.com/beacon.min.js"
      strategy="afterInteractive"
      data-cf-beacon={JSON.stringify({ token: analyticsToken, spa: true })}
    />}
  </body></html>;
}
