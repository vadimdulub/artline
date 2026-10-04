"use client";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useState } from "react";
import { useMemberSession } from "./MemberSession";
import { MemberNavigation, NavigationIcon } from "./MemberNavigation";
import "./SiteNavigation.css";
export function SiteHeader({ localDevelopment = false }: { localDevelopment?: boolean }) {
  const pathname = usePathname();
  const { session } = useMemberSession();
  const user = session?.user;
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  return <><header className="site-header" data-member={Boolean(user)}>
    <div className="site-brand">
    {user && <>
      <button type="button" className="member-menu-toggle member-menu-desktop" aria-label={collapsed ? "Show navigation" : "Hide navigation"} title={collapsed ? "Show navigation" : "Hide navigation"} aria-expanded={!collapsed} aria-controls="member-sidebar" onClick={() => setCollapsed(value => !value)}><NavigationIcon kind="menu" /></button>
      <button type="button" className="member-menu-toggle member-menu-mobile" aria-label="Open navigation" title="Open navigation" aria-expanded={drawerOpen} aria-controls="member-navigation-drawer" onClick={() => setDrawerOpen(true)}><NavigationIcon kind="menu" /></button>
    </>}
    <Link className="wordmark" href="/" aria-label="Artlines home">
      <Image className="wordmark-logo" src="/brand/artlines-wordmark.webp" width={576} height={138} alt="Artlines" loading="eager" unoptimized />
      <small>Art, literature &amp; history</small>
    </Link>
    </div>
    <nav className="primary-nav" aria-label="Primary navigation">
      <Link href="/" aria-current={pathname === "/" || pathname.startsWith("/artists") ? "page" : undefined}>Painters</Link>
      <Link href="/books" aria-current={pathname.startsWith("/books") ? "page" : undefined}>Books</Link>
      <Link href="/events" aria-current={pathname.startsWith("/events") ? "page" : undefined}>Events</Link>
      <Link href="/all" aria-current={pathname === "/all" ? "page" : undefined}>All</Link>
      {!user && <Link href="/account" aria-current={pathname === "/account" ? "page" : undefined}>Account</Link>}
    </nav>
    <div className="header-aside">{localDevelopment ? <Link href="/membership-preview">Membership ideas</Link> : <span>A personal study atlas</span>}{user ? <Link href="/account" className="help-link account-link" aria-label="Your account" title={user.name ? `Your account — ${user.name}` : "Your account"} aria-current={pathname === "/account" ? "page" : undefined}><NavigationIcon kind="user" /></Link> : <Link href="/about" className="help-link" aria-label="About this atlas">?</Link>}</div>
  </header>{user && <MemberNavigation collapsed={collapsed} drawerOpen={drawerOpen} closeDrawer={closeDrawer} />}</>;
}
