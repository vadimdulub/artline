"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useMemberSession } from "./MemberSession";
import { MemberNavigation, NavigationIcon } from "./MemberNavigation";
import "./SiteNavigation.css";

const accountRoutes = ["/artists", "/museums", "/account", "/art-history-timeline", "/coverage", "/about", "/membership-preview"];
export function SiteHeader() {
  const pathname = usePathname();
  const { session } = useMemberSession();
  const user = session?.user;
  const accountArea = accountRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  const [collapsed, setCollapsed] = useState(false);
  const closeMenu = useCallback(() => setCollapsed(true), []);
  const header = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!header.current) return;
    const observer = new ResizeObserver(([entry]) => {
      document.documentElement.style.setProperty("--measured-header-height", `${entry.target.getBoundingClientRect().height}px`);
    });
    observer.observe(header.current);
    return () => { observer.disconnect(); document.documentElement.style.removeProperty("--measured-header-height"); };
  }, []);
  const accountHref = user ? "/artists" : "/account";
  return <><header ref={header} className="site-header" data-member={Boolean(user)}>
    <div className="site-brand"><Link className="wordmark" href="/" aria-label="Artlines home">
      <Image className="wordmark-logo" src="/brand/artlines-wordmark.webp" width={576} height={138} alt="Artlines" loading="eager" unoptimized />
      <small>Art, literature &amp; history</small>
    </Link></div>
    <nav className="primary-nav" aria-label="Primary navigation">
      <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>Painters</Link>
      <Link href="/books" aria-current={pathname.startsWith("/books") ? "page" : undefined}>Books</Link>
      <Link href="/events" aria-current={pathname.startsWith("/events") ? "page" : undefined}>Events</Link>
      <Link href="/all" aria-current={pathname === "/all" ? "page" : undefined}>All</Link>
      <Link href={accountHref} prefetch={false} className="account-menu-link" aria-current={accountArea ? "page" : undefined} onClick={() => setCollapsed(false)}>Account</Link>
    </nav>
    <div className="header-aside">{user ? <Link href="/artists" prefetch={false} className="account-avatar" aria-label="Your account" title={user.name ? `Your account — ${user.name}` : "Your account"} onClick={() => setCollapsed(false)}><NavigationIcon kind="user" /></Link> : <Link href="/about" className="help-link" aria-label="About this atlas">?</Link>}</div>
  </header>{user && accountArea && <MemberNavigation open={!collapsed} close={closeMenu} show={() => setCollapsed(false)} />}</>;
}
