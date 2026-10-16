"use client";
import Image from "next/image";
import Link from "@/components/MemberLink";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useMemberSession } from "./MemberSession";
import { MemberNavigation, NavigationIcon } from "./MemberNavigation";
import { HeaderBackNavigation } from "./BackNavigation";
import { MobileNavigation } from "./MobileNavigation";
import "./SiteNavigation.css";

const accountRoutes = ["/studies", "/bookmarks", "/artists", "/artworks", "/museums", "/exhibitions", "/account", "/about", "/membership-preview"];
const panelPreferenceKey = "artline:account-panel-collapsed";
const mobileSections = [
  ["/books", "Books"], ["/events", "Events"], ["/all", "All"],
  ["/exhibitions", "Exhibitions"], ["/guides", "Guides"], ["/art-history-timeline", "Guides"],
  ["/artists", "Artists"], ["/artworks", "Artworks"], ["/museums", "Museums"],
  ["/studies", "Studies"], ["/shared/studies", "Studies"], ["/bookmarks", "Bookmarks"],
  ["/account", "Your account"], ["/about", "About"], ["/privacy", "Privacy"],
];
export function SiteHeader() {
  const pathname = usePathname();
  const mobileSection = pathname === "/" ? "Painters" : mobileSections.find(([route]) => pathname === route || pathname.startsWith(`${route}/`))?.[1] ?? "Artline";
  const { session } = useMemberSession();
  const user = session?.user;
  const guidesArea = pathname === "/guides" || pathname.startsWith("/guides/") || pathname.startsWith("/art-history-timeline");
  const accountArea = guidesArea || accountRoutes.some(route => pathname === route || pathname.startsWith(`${route}/`));
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
    <div className="header-brand"><HeaderBackNavigation />
    <div className="site-brand"><Link className="wordmark" href="/" aria-label="Artlines home">
      <Image className="wordmark-logo" src="/brand/artlines-wordmark.webp" width={576} height={138} alt="Artlines" loading="eager" unoptimized />
      <small>Art, literature &amp; history</small>
    </Link></div>
    <div className="mobile-brand">
      <Link className="mobile-home-link" href="/" aria-label="Artlines home">
        <svg viewBox="0 0 64 64" fill="currentColor" aria-hidden="true">
          <path d="M32 8h2l18 41c1.7 3.9 3.3 5.1 7 5.5V57H35v-2.5c7.2-.5 8.1-2.1 5.7-7.5L27 18.3Z" />
          <path d="M34 8 15 47c-2.4 5.2-2 7.2 6 7.5V57H5v-2.5c3.6-.5 5.5-2.6 8-7.5L32 8Z" />
          <path d="M11 38h31" fill="none" stroke="currentColor" strokeWidth="2" />
          <circle cx="26" cy="38" r="4.2" fill="var(--red)" />
        </svg>
      </Link>
      <span className="mobile-section-name">{mobileSection}</span>
    </div>
    </div>
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
