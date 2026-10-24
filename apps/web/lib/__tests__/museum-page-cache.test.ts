import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cachedMuseumPage, clearMuseumPageCache, rememberMuseumPage } from "../museum-page-cache";

beforeEach(() => { vi.useFakeTimers(); clearMuseumPageCache(); });
afterEach(() => { vi.useRealTimers(); clearMuseumPageCache(); });

it("reuses equivalent queries and expires pages after a minute", () => {
  rememberMuseumPage("museums?country=FR&q=Paris", { total: 1 });
  expect(cachedMuseumPage("museums?q=Paris&country=FR")).toEqual({ total: 1 });
  vi.advanceTimersByTime(60_000);
  expect(cachedMuseumPage("museums?q=Paris&country=FR")).toBeUndefined();
});

it("limits retained pages and rejects oversized responses", () => {
  for (let index = 0; index < 10; index++) rememberMuseumPage(`museums?cursor=${index}`, { total: index });
  expect(cachedMuseumPage("museums?cursor=0")).toBeUndefined();
  expect(cachedMuseumPage("museums?cursor=9")).toEqual({ total: 9 });
  rememberMuseumPage("museums?", "x".repeat(1 << 20));
  expect(cachedMuseumPage("museums?")).toBeUndefined();
});

it("never caches member records or artwork details and clears pages on sign-out", () => {
  rememberMuseumPage("museums?", { total: 1 });
  rememberMuseumPage("member/session", { user: "private" });
  rememberMuseumPage("museums/the-met/works", { title: "Artwork detail" });
  expect(cachedMuseumPage("member/session")).toBeUndefined();
  expect(cachedMuseumPage("museums/the-met/works")).toBeUndefined();
  window.dispatchEvent(new Event("artline:session-expired"));
  expect(cachedMuseumPage("museums?")).toBeUndefined();
});
