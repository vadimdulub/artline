"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function SiteHeader({ preview }: { preview: boolean }) {
  const pathname = usePathname();
  return <header className="site-header">
    <Link className="wordmark" href="/" aria-label="Artline home">
      <span className="atlas-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>Artline<small>Atlas of painters · 1100–2000</small></span>
    </Link>
    <nav className="primary-nav" aria-label="Primary navigation">
      <Link href="/" aria-current={pathname === "/" || pathname.startsWith("/artists") ? "page" : undefined}>Timeline</Link>
      <Link href="/museums" aria-current={pathname.startsWith("/museums") ? "page" : undefined}>Museums</Link>
      <Link href="/catalogue" aria-current={["/catalogue", "/coverage", "/imports"].some(path => pathname.startsWith(path)) ? "page" : undefined}>Catalogue</Link>
    </nav>
    <div className="header-aside"><span>{preview ? "Personal research preview" : "A personal study atlas"}</span><Link href="/about" className="help-link" aria-label="About this atlas">?</Link></div>
  </header>;
}
