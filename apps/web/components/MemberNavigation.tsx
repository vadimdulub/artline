"use client";

import Link from "@/components/MemberLink";
import { usePathname } from "next/navigation";

const groups = [
  { label: "Your collection", links: [{ href: "/bookmarks", label: "Bookmarks", icon: "star" }] },
  { label: "Explore", links: [{ href: "/artists", label: "Artists", icon: "artists" }, { href: "/artworks", label: "Artworks", icon: "artworks" }, { href: "/museums", label: "Museums", icon: "museum" }] },
  { label: "Resources", links: [{ href: "/art-history-timeline", label: "Art history guide", icon: "guide" }, { href: "/about", label: "About & sources", icon: "about" }] },
];

export function NavigationIcon({ kind }: { kind: string }) {
  const paths: Record<string, React.ReactNode> = {
    star: <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z" />,
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></>,
    menu: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></>,
    chevron: <path d="m14 6-6 6 6 6" />,
    artists: <><rect x="4" y="3" width="16" height="18" rx="1" /><circle cx="12" cy="9" r="2.5" /><path d="M7 18a5 5 0 0 1 10 0" /></>,
    artworks: <><rect x="3" y="3" width="18" height="18" rx="1" /><circle cx="8" cy="8" r="1.5" /><path d="m3 17 5-5 4 4 4-6 5 7" /></>,
    museum: <><path d="m3 8 9-5 9 5ZM3 21h18M5 10v8m7-8v8m7-8v8" /></>,
    guide: <><path d="M12 5v16M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3Z" /></>,
    about: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v1" /></>,
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[kind]}</svg>;
}

function NavigationLinks({ collapsed }: { collapsed: boolean }) {
  const pathname = usePathname();
  const current = (href: string) => pathname === href || pathname.startsWith(`${href}/`) ? "page" : undefined;
  return <nav id="member-navigation-links" aria-label="Member navigation">
    {groups.map(group => <div className="member-nav-group" role="group" aria-label={group.label} key={group.label}>{group.links.map(link => <Link key={link.href} href={link.href} prefetch={false} aria-current={current(link.href)} aria-label={link.label} title={collapsed ? link.label : undefined}><NavigationIcon kind={link.icon} /><span aria-hidden={collapsed}>{link.label}</span></Link>)}</div>)}
    <div className="member-nav-account"><Link href="/account" aria-current={current("/account")} aria-label="Your account" title={collapsed ? "Your account" : undefined}><NavigationIcon kind="user" /><span aria-hidden={collapsed}>Your account</span></Link></div>
  </nav>;
}

export function MemberNavigation({ open, close, show }: { open: boolean; close: () => void; show: () => void }) {
  return <aside id="member-sidebar" className="member-sidebar" data-collapsed={!open} aria-label="Account navigation" onKeyDown={event => {
    if (event.key === "Escape" && open) { close(); document.querySelector<HTMLAnchorElement>(".account-menu-link")?.focus({ preventScroll: true }); }
  }}>
    <NavigationLinks collapsed={!open} />
    <button type="button" className="member-panel-toggle" aria-label={open ? "Collapse account panel" : "Expand account panel"} title={open ? "Collapse account panel" : "Expand account panel"} aria-expanded={open} aria-controls="member-navigation-links" onClick={open ? close : show}><NavigationIcon kind="chevron" /></button>
  </aside>;
}
