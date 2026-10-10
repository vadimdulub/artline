import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { BookmarkClient, validBookmarkRef, type BookmarkRef } from "../bookmarks";
const upstream = vi.fn();
const ref = (n: number): BookmarkRef => ({ kind: n % 2 ? "artist" : "artwork", id: `11111111-1111-4111-8111-${String(n).padStart(12, "0")}` });
beforeEach(() => { vi.stubGlobal("fetch", upstream); upstream.mockReset(); });
afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
it("batches only the visible records, at most 100 references per request", async () => {
  vi.useFakeTimers();
  upstream.mockResolvedValue(Response.json({ saved: [] }));
  const client = new BookmarkClient("member");
  for (let i = 1; i <= 125; i++) client.subscribe(ref(i), () => {});
  await vi.advanceTimersByTimeAsync(40);
  expect(upstream).toHaveBeenCalledTimes(2);
  expect([...new URL(upstream.mock.calls[0][0], "https://artline.example").searchParams]).toHaveLength(100);
  expect([...new URL(upstream.mock.calls[1][0], "https://artline.example").searchParams]).toHaveLength(25);
  expect(client.get(ref(1))).toMatchObject({ ready: true, saved: false });
  client.dispose();
});
it("uses idempotent save/remove requests and shares the result between stars", async () => {
  upstream.mockResolvedValueOnce(Response.json({ saved: [] })).mockResolvedValueOnce(Response.json({ saved: true })).mockResolvedValueOnce(Response.json({ saved: false }));
  const client = new BookmarkClient("member"), changed = vi.fn();
  client.subscribe(ref(1), changed); client.subscribe(ref(1), changed);
  await client.toggle(ref(1));
  expect(client.get(ref(1)).saved).toBe(true);
  expect(upstream.mock.calls[1][1].method).toBe("PUT");
  await client.toggle(ref(1));
  expect(client.get(ref(1)).saved).toBe(false);
  expect(upstream.mock.calls[2][1].method).toBe("DELETE");
  expect(client.getRevision()).toBe(2);
  client.dispose();
});
it("a stale state response cannot undo a completed save", async () => {
  vi.useFakeTimers();
  let finish!: (value: Response) => void;
  upstream.mockImplementationOnce(() => new Promise(resolve => { finish = resolve; })).mockResolvedValueOnce(Response.json({ saved: true }));
  const client = new BookmarkClient("member"); client.subscribe(ref(1), () => {});
  await vi.advanceTimersByTimeAsync(35);
  await client.save(ref(1), true);
  finish(Response.json({ saved: [] }));
  await vi.advanceTimersByTimeAsync(1);
  expect(client.get(ref(1)).saved).toBe(true);
  client.dispose();
});
it("keeps the old value on write failure and permits an idempotent retry", async () => {
  const client = new BookmarkClient("member");
  upstream.mockResolvedValueOnce(Response.json({ error: { message: "Offline" } }, { status: 503 }));
  await expect(client.save(ref(1), true)).rejects.toThrow("Offline");
  expect(client.get(ref(1))).toMatchObject({ saved: false, busy: false, error: "Offline" });
  upstream.mockResolvedValueOnce(Response.json({ saved: true }));
  await client.save(ref(1), true);
  expect(client.get(ref(1))).toMatchObject({ saved: true, error: null });
  client.dispose();
});
it("clears access on an expired session without publishing another member's state", async () => {
  const expired = vi.fn(); window.addEventListener("artline:session-expired", expired);
  upstream.mockResolvedValue(Response.json({ error: { message: "Sign in" } }, { status: 401 }));
  const first = new BookmarkClient("member-a"), second = new BookmarkClient("member-b");
  await expect(first.save(ref(1), true)).rejects.toMatchObject({ status: 401 });
  expect(expired).toHaveBeenCalledTimes(1);
  expect(second.get(ref(1)).saved).toBe(false);
  expect(second.getRevision()).toBe(0);
  window.removeEventListener("artline:session-expired", expired);
  first.dispose(); second.dispose();
});
it("anonymous browsing performs no bookmark requests", async () => {
  vi.useFakeTimers();
  const client = new BookmarkClient(""); client.subscribe(ref(1), () => {});
  await vi.advanceTimersByTimeAsync(100);
  expect(upstream).not.toHaveBeenCalled();
  await expect(client.save(ref(1), true)).rejects.toMatchObject({ status: 401 });
  client.dispose();
});

it("refreshes visible saved states after another tab changes them", async () => {
  const client = new BookmarkClient("member");
  client.seedSaved([ref(1)]);
  const unsubscribe = client.subscribe(ref(1), () => {});
  upstream.mockResolvedValue(Response.json({ saved: [] }));
  await client.refresh();
  expect(client.get(ref(1))).toMatchObject({ saved: false, busy: false });
  expect(client.getRevision()).toBe(1);
  unsubscribe(); client.dispose();
});

it.each(["book", "event"] as const)("saves and restores %s states alongside artwork states", async kind => {
  const reference = { kind, id: "record-q123" };
  expect(validBookmarkRef(reference)).toBe(true);
  expect(validBookmarkRef({ kind, id: "../account" })).toBe(false);
  expect(validBookmarkRef({ kind, id: "x".repeat(161) })).toBe(false);
  expect(validBookmarkRef({ kind: "artist", id: reference.id })).toBe(false);
  upstream.mockResolvedValueOnce(Response.json({ saved: [reference] })).mockResolvedValueOnce(Response.json({ saved: false }));
  const client = new BookmarkClient("member");
  await client.toggle(reference);
  expect(upstream.mock.calls[0][0]).toBe(`/api/bookmarks/state?${kind}=record-q123`);
  expect(upstream.mock.calls[1][0]).toBe(`/api/bookmarks/${kind}/record-q123`);
  expect(upstream.mock.calls[1][1].method).toBe("DELETE");
  expect(client.get(reference)).toMatchObject({ saved: false, ready: true });
  client.dispose();
});
