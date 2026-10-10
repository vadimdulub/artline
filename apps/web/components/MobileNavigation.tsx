"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "./MemberLink";
import { NavigationIcon } from "./MemberNavigation";
import { lockBodyScroll } from "@/lib/modal-scroll";

const links = [
  { href: "/artists", label: "Artists", icon: "artists" },
  { href: "/artworks", label: "Artworks", icon: "artworks" },
  { href: "/museums", label: "Museums", icon: "museum" },
  { href: "/bookmarks", label: "Bookmarks", icon: "star" },
  { href: "/account", label: "Your account", icon: "user" },
  { href: "/art-history-timeline", label: "Art history guide", icon: "guide" },
  { href: "/about", label: "About & sources", icon: "about" },
];

export function MobileNavigation() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const element = dialog.current!;
    const opener = trigger.current;
    const unlock = lockBodyScroll();
    element.showModal();
    const desktop = window.matchMedia("(min-width: 761px)");
    const resize = () => { if (desktop.matches) setOpen(false); };
    desktop.addEventListener("change", resize);
    return () => {
      desktop.removeEventListener("change", resize);
      element.close();
      unlock();
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    };
  }, [open]);

  return <>
    <button ref={trigger} type="button" className="mobile-menu-toggle" aria-haspopup="dialog" aria-expanded={open} aria-controls="mobile-navigation" onClick={() => setOpen(true)}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>Menu
    </button>
    {open && <dialog ref={dialog} id="mobile-navigation" className="mobile-navigation" aria-labelledby="mobile-navigation-title" onCancel={event => { event.preventDefault(); setOpen(false); }} onClick={event => {
      if (event.target === event.currentTarget) {
        const box = event.currentTarget.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) setOpen(false);
      }
    }}>
      <header><h2 id="mobile-navigation-title">Explore Artline</h2><button type="button" onClick={() => setOpen(false)} autoFocus aria-label="Close menu">×</button></header>
      <nav aria-label="Explore Artline" onClick={event => {
        // A member link may open sign-in above this menu. Keep its return focus target.
        if (!event.defaultPrevented && event.target instanceof Element && event.target.closest("a")) setOpen(false);
      }}>
        {links.map(link => <Link key={link.href} href={link.href} prefetch={false} aria-current={pathname === link.href || pathname.startsWith(`${link.href}/`) ? "page" : undefined}><NavigationIcon kind={link.icon} /><span>{link.label}</span></Link>)}
      </nav>
    </dialog>}
  </>;
}
