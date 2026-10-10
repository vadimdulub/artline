import { ApiError } from "./api";
export type BookmarkKind = "artist" | "artwork";
export type BookmarkRef = { kind: BookmarkKind; id: string };
export type BookmarkItem = BookmarkRef & { title: string; subtitle: string; href: string; saved_at: string; media_url: string | null; alt_text: string | null; rights_status: string | null };
export type BookmarkPage = { items: BookmarkItem[]; next_cursor: string };
export const bookmarkKey = (ref: BookmarkRef) => `${ref.kind}:${ref.id}`;
export const validBookmarkRef = (value: unknown): value is BookmarkRef => {
  if (!value || typeof value !== "object") return false;
  const ref = value as BookmarkRef;
  return ["artist", "artwork"].includes(ref.kind) && typeof ref.id === "string" && /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(ref.id);
};
export async function bookmarkRequest<T>(path = "", options: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/bookmarks${path}`, { ...options, cache: "no-store" });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event("artline:session-expired"));
    throw new ApiError(body?.error?.message ?? "Your bookmarks are temporarily unavailable. Please try again.", response.status);
  }
  return body as T;
}
type BookmarkState = { saved: boolean; busy: boolean; ready: boolean; error: string | null };
const empty: BookmarkState = { saved: false, busy: false, ready: true, error: null };
const loading: BookmarkState = { saved: false, busy: true, ready: false, error: null };

// A session owns one bounded UI cache. Mounted stars share batched state reads;
// mutations are idempotent and stale reads cannot overwrite a completed save.
export class BookmarkClient {
  private states = new Map<string, BookmarkState>();
  private versions = new Map<string, number>();
  private listeners = new Map<string, Set<() => void>>();
  private refs = new Map<string, BookmarkRef>();
  private changes = new Set<() => void>();
  private revision = 0;
  private refreshing = false;
  private timer: ReturnType<typeof setTimeout> | undefined;
  private controller = new AbortController();
  constructor(readonly owner: string) {}
  activate() {
    if (this.controller.signal.aborted) {
      this.controller = new AbortController();
      for (const [key, value] of this.states) if (value.busy) this.states.delete(key);
      this.timer = setTimeout(() => { this.timer = undefined; void this.loadMounted(); }, 30);
    }
  }
  get = (ref: BookmarkRef) => this.owner ? this.states.get(bookmarkKey(ref)) ?? loading : empty;
  seedSaved(refs: BookmarkRef[]) {
    for (const ref of refs) {
      const key = bookmarkKey(ref);
      if ((this.versions.get(key) ?? 0) === 0 && !this.states.get(key)?.ready) {
        this.versions.set(key, 1);
        this.update(ref, { ...empty, saved: true });
      }
    }
  }
  getRevision = () => this.revision;
  subscribeChanges = (listener: () => void) => { this.changes.add(listener); return () => { this.changes.delete(listener); }; };
  subscribe(ref: BookmarkRef, listener: () => void) {
    const key = bookmarkKey(ref);
    const listeners = this.listeners.get(key) ?? new Set();
    listeners.add(listener); this.listeners.set(key, listeners); this.refs.set(key, ref);
    if (this.owner && !this.states.has(key) && !this.timer) this.timer = setTimeout(() => { this.timer = undefined; void this.loadMounted(); }, 30);
    return () => {
      listeners.delete(listener);
      if (!listeners.size) { this.listeners.delete(key); this.refs.delete(key); }
      if (this.states.size > 500) for (const stored of this.states.keys()) {
        if (!this.listeners.has(stored)) { this.states.delete(stored); this.versions.delete(stored); }
        if (this.states.size <= 500) break;
      }
    };
  }
  private update(ref: BookmarkRef, state: BookmarkState) {
    if (this.controller.signal.aborted) return;
    const key = bookmarkKey(ref); this.states.set(key, state);
    this.listeners.get(key)?.forEach(listener => listener());
  }
  async refresh() {
    if (!this.owner || this.refreshing || this.controller.signal.aborted) return;
    this.refreshing = true;
    const refs = [...this.refs.values()].filter(ref => !this.get(ref).busy);
    try { for (let offset = 0; offset < refs.length; offset += 100) await this.load(refs.slice(offset, offset + 100)); }
    finally {
      this.refreshing = false;
      if (!this.controller.signal.aborted) { this.revision++; this.changes.forEach(listener => listener()); }
    }
  }
  private async loadMounted() {
    const refs = [...this.refs.values()].filter(ref => !this.states.has(bookmarkKey(ref)));
    for (let offset = 0; offset < refs.length; offset += 100) await this.load(refs.slice(offset, offset + 100));
  }
  private async load(refs: BookmarkRef[]) {
    if (!refs.length || this.controller.signal.aborted) return;
    const controller = this.controller;
    const versions = refs.map(ref => this.versions.get(bookmarkKey(ref)) ?? 0);
    const query = new URLSearchParams();
    refs.forEach(ref => { query.append(ref.kind, ref.id); this.update(ref, { ...this.get(ref), busy: true, ready: false, error: null }); });
    try {
      const result = await bookmarkRequest<{ saved: BookmarkRef[] }>(`/state?${query}`, { signal: controller.signal });
      if (controller.signal.aborted) return;
      const saved = new Set(result.saved.map(bookmarkKey));
      refs.forEach((ref, i) => { if ((this.versions.get(bookmarkKey(ref)) ?? 0) === versions[i]) this.update(ref, { ...empty, saved: saved.has(bookmarkKey(ref)) }); });
    } catch (error) {
      if (controller.signal.aborted) return;
      refs.forEach((ref, i) => { if ((this.versions.get(bookmarkKey(ref)) ?? 0) === versions[i]) this.update(ref, { ...empty, ready: false, error: error instanceof Error ? error.message : "Couldn’t load bookmarks." }); });
    }
  }
  async toggle(ref: BookmarkRef) {
    if (!this.get(ref).ready) await this.load([ref]);
    const current = this.get(ref);
    if (!current.ready) throw new Error(current.error ?? "Couldn’t load bookmarks.");
    if (current.busy) return;
    await this.save(ref, !current.saved);
  }
  async save(ref: BookmarkRef, saved: boolean) {
    if (!this.owner) throw new ApiError("Sign in to save bookmarks.", 401);
    const controller = this.controller;
    const key = bookmarkKey(ref), previous = this.get(ref);
    this.versions.set(key, (this.versions.get(key) ?? 0) + 1);
    this.update(ref, { ...previous, busy: true, error: null });
    try {
      const result = await bookmarkRequest<{ saved: boolean }>(`/${ref.kind}/${ref.id}`, { method: saved ? "PUT" : "DELETE", signal: controller.signal });
      if (controller.signal.aborted) throw new DOMException("Aborted", "AbortError");
      this.update(ref, { ...empty, saved: result.saved });
      this.revision++; this.changes.forEach(listener => listener());
    } catch (error) {
      if (controller.signal.aborted) throw error;
      this.update(ref, { ...previous, busy: false, error: error instanceof Error ? error.message : "Couldn’t update bookmarks." });
      throw error;
    }
  }
  dispose() { clearTimeout(this.timer); this.controller.abort(); }
}
