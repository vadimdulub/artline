"use client";

import { useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "@/components/MemberLink";
import "./BackNavigation.css";

export function backDestination(pathname: string): string {
  if (/^\/artists\/[^/]+\/works\/[^/]+/.test(pathname)) return pathname.split("/works/")[0];
  if (pathname.startsWith("/artists/")) return "/artists";
  if (pathname.startsWith("/museums/")) return "/museums";
  if (pathname.startsWith("/guides/")) return "/guides";
  if (pathname.startsWith("/studies/")) return "/studies";
  return "/";
}

function parentLabel(pathname: string) {
  if (/^\/artists\/[^/]+\/works\/[^/]+/.test(pathname)) return "Artist";
  if (pathname.startsWith("/artists/")) return "All artists";
  if (pathname.startsWith("/museums/")) return "All museums";
  if (pathname.startsWith("/guides/")) return "All guides";
  if (pathname.startsWith("/studies/")) return "Your studies";
  return "Explore the timeline";
}

const listeners = new Set<() => void>();
let stopTracking: (() => void) | undefined;
const notify = () => listeners.forEach(listener => listener());
const hasReturnHistory = () => window.history.state?.artlineCanGoBack === true && window.history.length > 1;
const noServerHistory = () => false;

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (listeners.size === 1) {
    const originalPush = window.history.pushState;
    const originalReplace = window.history.replaceState;
    const push: History["pushState"] = function (this: History, data, unused, url) {
      const internal = !url || new URL(url, window.location.href).origin === window.location.origin;
      originalPush.call(this, internal ? { ...data, artlineCanGoBack: true } : data, unused, url);
      notify();
    };
    const replace: History["replaceState"] = function (this: History, data, unused, url) {
      const marker = window.history.state?.artlineCanGoBack === true;
      originalReplace.call(this, marker ? { ...data, artlineCanGoBack: true } : data, unused, url);
      notify();
    };
    window.history.pushState = push;
    window.history.replaceState = replace;
    window.addEventListener("popstate", notify);
    if (document.referrer && new URL(document.referrer).origin === window.location.origin) {
      window.history.replaceState({ ...window.history.state, artlineCanGoBack: true }, "");
    }
    stopTracking = () => {
      if (window.history.pushState === push) window.history.pushState = originalPush;
      if (window.history.replaceState === replace) window.history.replaceState = originalReplace;
      window.removeEventListener("popstate", notify);
    };
  }
  return () => {
    listeners.delete(listener);
    if (listeners.size === 0) { stopTracking?.(); stopTracking = undefined; }
  };
}

function Arrow() {
  return <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m12 5-7 7 7 7M5 12h14" /></svg>;
}

function ReturnLink({ className, canGoBack, pathname }: { className: string; canGoBack: boolean; pathname: string }) {
  const router = useRouter();
  const label = canGoBack ? "Back" : parentLabel(pathname);
  return <Link className={className} aria-label={label} title={label} href={backDestination(pathname)} prefetch={false} onClick={event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (canGoBack && hasReturnHistory()) { event.preventDefault(); router.back(); }
  }}><Arrow /><span>{label}</span></Link>;
}

/** The mobile header keeps one consistent, reachable return control. */
export function BackNavigation() {
  const pathname = usePathname();
  const canGoBack = useSyncExternalStore(subscribe, hasReturnHistory, noServerHistory);
  if (pathname === "/" && !canGoBack) return null;
  return <ReturnLink className="site-back" pathname={pathname} canGoBack={canGoBack} />;
}

/** Desktop return navigation sits above the content, outside the brand header. */
export function PageBackNavigation() {
  const pathname = usePathname();
  const canGoBack = useSyncExternalStore(subscribe, hasReturnHistory, noServerHistory);
  const artwork = /^\/artists\/[^/]+\/works\/[^/]+/.test(pathname);
  // Record templates already provide their own named directory/breadcrumb links.
  const hasParentLink = !artwork && /^\/(artists|museums|guides|studies)\//.test(pathname);
  const showParent = pathname !== "/" && !hasParentLink;
  if (!canGoBack && !showParent) return null;
  const family = pathname.startsWith("/guides/") ? "guide" : ["/privacy", "/art-history-timeline"].includes(pathname) ? "prose" : pathname.startsWith("/studies") || pathname.startsWith("/shared/studies/") ? "study" : "standard";
  return <nav className="page-return-nav" aria-label="Return navigation" data-family={family}>
    {canGoBack && <ReturnLink className="page-back" pathname={pathname} canGoBack />}
    {showParent && <Link className="page-parent" href={backDestination(pathname)} prefetch={false}>{parentLabel(pathname)}</Link>}
  </nav>;
}
