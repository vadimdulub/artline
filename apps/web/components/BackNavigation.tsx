"use client";

import { useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "@/components/MemberLink";
import { useMemberSession } from "./MemberSession";
import { requiresMember } from "@/lib/member-return";
import "./BackNavigation.css";

type ReturnTarget = { href: string; label: string };
type PendingReturn = { from: ReturnTarget; to: string; at: number };
const storageKey = "artline:return-navigation";

export function backDestination(pathname: string): string {
  if (/^\/artists\/[^/]+\/works\/[^/]+/.test(pathname)) return pathname.split("/works/")[0];
  if (pathname.startsWith("/artists/")) return "/artists";
  if (pathname.startsWith("/museums/")) return "/museums";
  if (pathname.startsWith("/guides/") || pathname.startsWith("/art-history-timeline")) return "/guides";
  if (pathname.startsWith("/exhibitions/")) return "/exhibitions";
  if (pathname.startsWith("/studies/")) return "/studies";
  return "/";
}

function parentLabel(pathname: string) {
  if (/^\/artists\/[^/]+\/works\/[^/]+/.test(pathname)) return "View artist";
  if (pathname.startsWith("/artists/")) return "All artists";
  if (pathname.startsWith("/museums/")) return "All museums";
  if (pathname.startsWith("/guides/") || pathname.startsWith("/art-history-timeline")) return "All guides";
  if (pathname.startsWith("/exhibitions/")) return "All exhibitions";
  if (pathname.startsWith("/studies/")) return "Your studies";
  return "Explore the timeline";
}

function internalHref(value: unknown): string | null {
  if (typeof value !== "string" || !value || value.length > 4096) return null;
  try {
    const url = new URL(value, window.location.href);
    return url.origin === window.location.origin ? url.pathname + url.search + url.hash : null;
  } catch { return null; }
}
function target(value: unknown): ReturnTarget | null {
  if (!value || typeof value !== "object") return null;
  const { href, label } = value as Partial<ReturnTarget>;
  const safe = internalHref(href);
  return safe && typeof label === "string" && label.trim() ? { href: safe, label: label.trim().slice(0, 100) } : null;
}
function routeLabel(pathname: string): string {
  const pages: Record<string, string> = { "/": "timeline", "/books": "Books", "/events": "Events", "/all": "All", "/artists": "artists", "/artworks": "artworks", "/museums": "museums", "/guides": "guides", "/studies": "your studies", "/bookmarks": "bookmarks", "/about": "About", "/privacy": "Privacy", "/account": "your account", "/catalogue": "catalogue", "/art-history-timeline": "art history timeline" };
  if (pages[pathname]) return pages[pathname];
  if (pathname.startsWith("/guides/")) return "guide";
  if (pathname.startsWith("/art-history-timeline/")) return "art history timeline";
  if (pathname.includes("/works/")) return "artwork";
  if (pathname.startsWith("/artists/")) return "artist";
  if (pathname.startsWith("/museums/")) return "museum";
  if (pathname.startsWith("/studies/") || pathname.startsWith("/shared/studies/")) return "study";
  return "previous page";
}
function currentPage(): ReturnTarget {
  const main = document.getElementById("main-content");
  const label = main?.dataset.returnPath === window.location.pathname ? main.dataset.returnLabel : null;
  return { href: window.location.pathname + window.location.search + window.location.hash, label: label?.trim().slice(0, 100) || routeLabel(window.location.pathname) };
}

const listeners = new Set<() => void>();
let stopTracking: (() => void) | undefined;
let pending: PendingReturn | null = null;
const notify = () => listeners.forEach(listener => listener());
const snapshot = () => JSON.stringify(window.history.length > 1 ? target(window.history.state?.artlineReturn) : null);
const serverSnapshot = () => "null";

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (listeners.size === 1) {
    const originalPush = window.history.pushState;
    const originalReplace = window.history.replaceState;
    const rememberClick = (event: MouseEvent) => {
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const link = event.target instanceof Element ? event.target.closest("a") : null;
      if (!link || link.hasAttribute("download") || (link.target && link.target !== "_self")) return;
      const to = internalHref(link.href);
      if (!to) return;
      pending = { from: currentPage(), to, at: Date.now() };
      // Plain anchors also need the source name after a full document navigation.
      try { sessionStorage.setItem(storageKey, JSON.stringify(pending)); } catch { /* History remains usable without storage. */ }
    };
    const push: History["pushState"] = function (this: History, data, unused, url) {
      const to = internalHref(url ? String(url) : window.location.href);
      const from = pending && pending.to === to && pending.from.href === currentPage().href && Date.now() - pending.at < 15000 ? pending.from : currentPage();
      const previous = to && new URL(to, window.location.origin).pathname === window.location.pathname ? { ...from, label: "previous view" } : from;
      originalPush.call(this, to ? { ...data, artlineCanGoBack: true, artlineReturn: previous, artlineReturnInitialized: true } : data, unused, url);
      pending = null;
      // Next writes history during its insertion effect; notify after that commit.
      queueMicrotask(notify);
    };
    const replace: History["replaceState"] = function (this: History, data, unused, url) {
      const previous = target(window.history.state?.artlineReturn);
      originalReplace.call(this, { ...data, ...(previous ? { artlineCanGoBack: true, artlineReturn: previous } : {}), artlineReturnInitialized: true }, unused, url);
      queueMicrotask(notify);
    };
    window.history.pushState = push;
    window.history.replaceState = replace;
    window.addEventListener("popstate", notify);
    document.addEventListener("click", rememberClick, true);
    if (!window.history.state?.artlineReturnInitialized) {
      const referrer = internalHref(document.referrer);
      let previous = target(window.history.state?.artlineReturn);
      if (!previous && referrer && window.history.length > 1) {
        let saved: PendingReturn | null = null;
        try { saved = JSON.parse(sessionStorage.getItem(storageKey) || "null"); } catch { /* Use a route-level label. */ }
        const from = target(saved?.from);
        previous = from && from.href === referrer && saved?.to === currentPage().href && Date.now() - saved.at < 15000
          ? from : { href: referrer, label: routeLabel(new URL(referrer, window.location.origin).pathname) };
      }
      originalReplace.call(window.history, { ...window.history.state, ...(previous ? { artlineReturn: previous, artlineCanGoBack: true } : {}), artlineReturnInitialized: true }, "");
    }
    stopTracking = () => {
      if (window.history.pushState === push) window.history.pushState = originalPush;
      if (window.history.replaceState === replace) window.history.replaceState = originalReplace;
      window.removeEventListener("popstate", notify);
      document.removeEventListener("click", rememberClick, true);
      pending = null;
    };
  }
  return () => { listeners.delete(listener); if (listeners.size === 0) { stopTracking?.(); stopTracking = undefined; } };
}
function useReturnTarget(): ReturnTarget | null {
  return JSON.parse(useSyncExternalStore(subscribe, snapshot, serverSnapshot));
}
function Arrow() {
  return <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m12 5-7 7 7 7M5 12h14" /></svg>;
}

/** One return control for every page, beside the logo. */
export function HeaderBackNavigation() {
  const pathname = usePathname();
  const previous = useReturnTarget();
  const router = useRouter();
  const { session } = useMemberSession();
  if (pathname === "/" && !previous) return <button className="header-back" type="button" aria-label="Go back" disabled><Arrow /></button>;
  const href = previous?.href || backDestination(pathname);
  const title = previous ? `Back to ${previous.label}` : parentLabel(pathname);
  return <Link className="header-back" aria-label="Go back" title={title} href={href} prefetch={false} onClick={event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    // Let MemberLink open its sign-in prompt for protected return destinations.
    if (requiresMember(href) && !session?.user?.id) return;
    if (previous && snapshot() === JSON.stringify(previous)) { event.preventDefault(); router.back(); }
  }}><Arrow /></Link>;
}
