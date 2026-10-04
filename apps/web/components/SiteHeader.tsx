"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useState } from "react";
import { useMemberSession } from "./MemberSession";
import { MemberNavigation } from "./MemberNavigation";
import "./SiteNavigation.css";
export function SiteHeader({ localDevelopment = false }: { localDevelopment?: boolean }) {
  const pathname = usePathname();
  const { session } = useMemberSession();
  const user = session?.user;
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = useCallback(() => setMenuOpen(false), []);
  return <><header className="site-header" data-member={Boolean(user)}>
    <div className="site-brand">
    <Link className="wordmark" href="/" aria-label="Artlines home" onClick={closeMenu}>
      <Image className="wordmark-logo" src="/brand/artlines-wordmark.webp" width={576} height={138} alt="Artlines" loading="eager" unoptimized />
      <small>Art, literature &amp; history</small>
    </Link>
    </div>
    <nav className="primary-nav" aria-label="Primary navigation" onClick={event => { if ((event.target as Element).closest("a")) closeMenu(); }}>
      <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>Painters</Link>
      <Link href="/artists" aria-current={pathname.startsWith("/artists") ? "page" : undefined}>Artists</Link>
      <Link href="/books" aria-current={pathname.startsWith("/books") ? "page" : undefined}>Books</Link>
      <Link href="/events" aria-current={pathname.startsWith("/events") ? "page" : undefined}>Events</Link>
      <Link href="/all" aria-current={pathname === "/all" ? "page" : undefined}>All</Link>
      {user ? <button type="button" className="account-menu-toggle" aria-expanded={menuOpen} aria-controls="member-sidebar member-navigation-drawer" onClick={() => setMenuOpen(value => !value)} onKeyDown={event => { if (event.key === "Escape") closeMenu(); }}>Account</button> : <Link href="/account" aria-current={pathname === "/account" ? "page" : undefined}>Account</Link>}
    </nav>
    <div className="header-aside">{localDevelopment ? <Link href="/membership-preview" onClick={closeMenu}>Membership ideas</Link> : <span>A personal study atlas</span>}{!user && <Link href="/about" className="help-link" aria-label="About this atlas">?</Link>}</div>
  </header>{user && <MemberNavigation open={menuOpen} close={closeMenu} />}</>;
}
