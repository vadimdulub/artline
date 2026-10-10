"use client";
import Image from "next/image";
import Link from "@/components/MemberLink";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useMemberSession } from "./MemberSession";
import { MemberNavigation, NavigationIcon } from "./MemberNavigation";
import { MobileNavigation } from "./MobileNavigation";
import "./SiteNavigation.css";

const accountRoutes = ["/bookmarks", "/artists", "/artworks", "/museums", "/account", "/about", "/membership-preview"];
const panelPreferenceKey = "artline:account-panel-collapsed";
export function SiteHeader() {
  const pathname = usePathname();
  const { session } = useMemberSession();
  const user = session?.user;
  const accountArea = accountRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
  const guidesArea = pathname === "/guides" || pathname.startsWith("/guides/") || pathname === "/art-history-timeline";
  // The session guard keeps this browser preference out of the server-rendered UI.
  const [collapsed, setCollapsed] = useState(() => {
    try { return typeof window !== "undefined" && localStorage.getItem(panelPreferenceKey) === "1"; }
    catch { return false; }
  });
  const closeMenu = useCallback(() => setCollapsed(true), []);
  const header = useRef<HTMLElement>(null);
  useEffect(() => {
    try { localStorage.setItem(panelPreferenceKey, collapsed ? "1" : "0"); }
    catch { /* Navigation still works when browser storage is unavailable. */ }
  }, [collapsed]);
  useEffect(() => {
    if (!header.current) return;
    const observer = new ResizeObserver(([entry]) => {
      document.documentElement.style.setProperty("--measured-header-height", `${entry.target.getBoundingClientRect().height}px`);
    });
    observer.observe(header.current);
    return () => { observer.disconnect(); document.documentElement.style.removeProperty("--measured-header-height"); };
  }, []);
  return <><header ref={header} className="site-header" data-member={Boolean(user)}>
    <div className="site-brand"><Link className="wordmark" href="/" aria-label="Artlines home">
      <Image className="wordmark-logo" src="/brand/artlines-wordmark.webp" width={576} height={138} alt="Artlines" loading="eager" unoptimized />
      <small>Art, literature &amp; history</small>
    </Link></div>
    <nav className="primary-nav" aria-label="Primary navigation">
      <div className="explore-nav">
        <Link href="/" aria-current={pathname === "/" ? "page" : undefined}>Painters</Link>
        <Link href="/books" aria-current={pathname === "/books" || pathname.startsWith("/books/") ? "page" : undefined}>Books</Link>
        <Link href="/events" aria-current={pathname === "/events" || pathname.startsWith("/events/") ? "page" : undefined}>Events</Link>
        <Link href="/all" aria-current={pathname === "/all" ? "page" : undefined}>All</Link>
      </div>
      <span className="primary-nav-divider" aria-hidden="true" />
      <Link href="/guides" className="guides-nav-link" aria-current={guidesArea ? "page" : undefined}>Guides</Link>
    </nav>
    <MobileNavigation key={pathname} />
    <div className="header-aside"><Link href="/account" prefetch={false} className="account-avatar account-menu-link" aria-label="Your account" aria-current={pathname === "/account" ? "page" : undefined} title={user?.name ? `Your account — ${user.name}` : "Your account"}><NavigationIcon kind="user" /></Link></div>
  </header>{user && accountArea && <MemberNavigation open={!collapsed} close={closeMenu} show={() => setCollapsed(false)} />}</>;
}
