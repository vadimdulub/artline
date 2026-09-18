"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function SiteHeader({ preview }: { preview: boolean }) {
  const pathname = usePathname();
  return <header className="site-header">
    <Link className="wordmark" href="/" aria-label="Artline home">
      <span className="atlas-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>Artline<small>Art, literature &amp; history</small></span>
    </Link>
    <nav className="primary-nav" aria-label="Primary navigation">
      <Link href="/" aria-current={pathname === "/" || pathname.startsWith("/artists") ? "page" : undefined}>Painters</Link>
      <Link href="/books" aria-current={pathname.startsWith("/books") ? "page" : undefined}>Books</Link>
      <Link href="/events" aria-current={pathname.startsWith("/events") ? "page" : undefined}>Events</Link>
      <Link href="/all" aria-current={pathname === "/all" ? "page" : undefined}>All</Link>
    </nav>
    <div className="header-aside"><span>{preview ? "Personal research preview" : "A personal study atlas"}</span><Link href="/about" className="help-link" aria-label="About this atlas">?</Link></div>
  </header>;
}
