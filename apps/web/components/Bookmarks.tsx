"use client";
import { createContext, useContext, useEffect, useMemo, useSyncExternalStore, type ReactNode } from "react";
import { ApiError } from "@/lib/api";
import { BookmarkClient, validBookmarkRef, type BookmarkKind, type BookmarkRef } from "@/lib/bookmarks";
import { memberReturnTo } from "@/lib/member-return";
import { useMemberSession } from "./MemberSession";
import { useRequestSignIn } from "./MemberLink";

const Bookmarks = createContext<BookmarkClient | null>(null);
const anonymous = new BookmarkClient("");
const pendingKey = "artline:pending-bookmark";
export const useBookmarks = () => useContext(Bookmarks) ?? anonymous;
export function BookmarkProvider({ children }: { children: ReactNode }) {
  const { session } = useMemberSession();
  const owner = session?.user?.id ?? "";
  const client = useMemo(() => new BookmarkClient(owner), [owner]);
  useEffect(() => {
    client.activate();
    const refresh = () => { if (document.visibilityState === "visible") void client.refresh(); };
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => { client.dispose(); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); };
  }, [client]);
  useEffect(() => {
    if (!owner) return;
    try {
      const pending = JSON.parse(sessionStorage.getItem(pendingKey) ?? "null");
      if (!pending) return;
      if (!validBookmarkRef(pending.ref) || typeof pending.at !== "number" || Date.now() - pending.at < 0 || Date.now() - pending.at >= 900000) { sessionStorage.removeItem(pendingKey); return; }
      void client.save(pending.ref, true).then(() => { if (sessionStorage.getItem(pendingKey) === JSON.stringify(pending)) sessionStorage.removeItem(pendingKey); }).catch(() => { /* The star exposes the failure and allows a retry. */ });
    } catch { /* Browsing and manual saving work without session storage. */ }
  }, [client, owner]);
  return <Bookmarks.Provider value={client}>{children}</Bookmarks.Provider>;
}
export function StarIcon({ filled = false }: { filled?: boolean }) {
  return <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z" /></svg>;
}
export function BookmarkButton({ kind, id, title }: { kind: BookmarkKind; id: string; title: string }) {
  const client = useBookmarks(), signIn = useRequestSignIn();
  const ref = useMemo<BookmarkRef>(() => ({ kind, id }), [kind, id]);
  const subscribe = useMemo(() => (listener: () => void) => client.subscribe(ref, listener), [client, ref]);
  const state = useSyncExternalStore(subscribe, () => client.get(ref), () => anonymous.get(ref));
  const label = `${state.saved ? "Remove" : "Save"} ${title} ${state.saved ? "from" : "to"} bookmarks`;
  function login(trigger: HTMLElement) {
    try { sessionStorage.setItem(pendingKey, JSON.stringify({ ref, at: Date.now() })); } catch { /* Saving remains available after signing in. */ }
    const destination = memberReturnTo(window.location.pathname + window.location.search + window.location.hash) ?? "/bookmarks";
    signIn?.(destination, trigger, { bookmark: true, onDismiss: () => { try { sessionStorage.removeItem(pendingKey); } catch { /* Storage may be disabled. */ } } });
  }
  return <span className="bookmark-control">
    <button className="bookmark-button" type="button" aria-label={label} title={label} aria-pressed={state.saved} aria-busy={state.busy} disabled={Boolean(client.owner) && state.busy} onClick={event => {
      event.preventDefault(); event.stopPropagation();
      const trigger = event.currentTarget;
      if (!client.owner) { login(trigger); return; }
      void client.toggle(ref).catch(error => { if (error instanceof ApiError && error.status === 401) login(trigger); });
    }}><StarIcon filled={state.saved} /></button>
    {state.error && <span className="bookmark-error" role="alert">{state.error}</span>}
  </span>;
}
