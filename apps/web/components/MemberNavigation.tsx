"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef } from "react";
import { lockBodyScroll } from "@/lib/modal-scroll";

const groups = [
  { label: "Collection", links: [{ href: "/artists", label: "Artists", icon: "artists" }, { href: "/museums", label: "Museums", icon: "museum" }] },
  { label: "Resources", links: [{ href: "/art-history-timeline", label: "Art history guide", icon: "guide" }, { href: "/coverage", label: "Collection coverage", icon: "coverage" }, { href: "/about", label: "About & sources", icon: "about" }] },
];

export function NavigationIcon({ kind }: { kind: string }) {
  const paths: Record<string, React.ReactNode> = {
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></>,
    menu: <><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M9 4v16" /></>,
    artists: <><rect x="4" y="3" width="16" height="18" rx="1" /><circle cx="12" cy="9" r="2.5" /><path d="M7 18a5 5 0 0 1 10 0" /></>,
    museum: <><path d="m3 8 9-5 9 5ZM3 21h18M5 10v8m7-8v8m7-8v8" /></>,
    guide: <><path d="M12 5v16M3 4h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v15h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3Z" /></>,
    coverage: <><path d="M4 4v16h17M8 16v-4m5 4V7m5 9V4" /></>,
    about: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v1" /></>,
  };
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[kind]}</svg>;
}

function NavigationLinks({ close }: { close?: () => void }) {
  const pathname = usePathname();
  const current = (href: string) => pathname === href || pathname.startsWith(`${href}/`) ? "page" : undefined;
  return <nav aria-label="Member navigation">
    {groups.map(group => <div className="member-nav-group" key={group.label}><p>{group.label}</p>{group.links.map(link => <Link key={link.href} href={link.href} prefetch={false} aria-current={current(link.href)} onClick={close}><NavigationIcon kind={link.icon} /><span>{link.label}</span></Link>)}</div>)}
    <div className="member-nav-account"><Link href="/account" aria-current={current("/account")} onClick={close}><NavigationIcon kind="user" /><span>Your account</span></Link></div>
  </nav>;
}

export function MemberNavigation({ collapsed, drawerOpen, closeDrawer }: { collapsed: boolean; drawerOpen: boolean; closeDrawer: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (!drawerOpen || !dialog.current) return;
    const element = dialog.current;
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const unlock = lockBodyScroll();
    element.showModal();
    const desktop = window.matchMedia("(min-width: 1101px)");
    const resize = () => { if (desktop.matches) closeDrawer(); };
    desktop.addEventListener("change", resize);
    return () => {
      desktop.removeEventListener("change", resize);
      element.close(); unlock();
      if (previousFocus?.isConnected && previousFocus.getClientRects().length) previousFocus.focus({ preventScroll: true });
      else document.querySelector<HTMLButtonElement>(".member-menu-desktop")?.focus({ preventScroll: true });
    };
  }, [drawerOpen, closeDrawer]);

  return <>
    <aside id="member-sidebar" className="member-sidebar" data-collapsed={collapsed} aria-label="Collection navigation"><NavigationLinks /></aside>
    <dialog ref={dialog} id="member-navigation-drawer" className="member-navigation-drawer" aria-labelledby="member-navigation-title"
      onCancel={event => { event.preventDefault(); closeDrawer(); }} onClick={event => {
        if (event.target !== event.currentTarget) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeDrawer();
      }}>
      <div className="member-navigation-heading"><h2 id="member-navigation-title">Explore Artlines</h2><button type="button" aria-label="Close navigation" onClick={closeDrawer} autoFocus>×</button></div>
      <NavigationLinks close={closeDrawer} />
    </dialog>
  </>;
}
