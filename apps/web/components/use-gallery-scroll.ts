"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { apiRequest } from "@/lib/api";
export type GalleryPage<T> = { items: T[]; nextCursor: string };

type Page = { cursor: string; start: number; count: number; next: string };
type Window<T> = { items: T[]; before: number; after: number; loading: boolean; failed: boolean; complete: boolean };

// Keep three server pages around the viewport. Earlier pages can be fetched again
// using their cursors; only the small cursor index grows with a browsing session.
export function useGalleryScroll<T, R>(strip: RefObject<HTMLUListElement | null>, initial: GalleryPage<T>, query: string, busy: boolean, endpoint: string, cursorKey: string, readPage: (response: R) => GalleryPage<T>) {
  const [window, setWindow] = useState<Window<T>>({ items: initial.items, before: 0, after: 0, loading: false, failed: false, complete: !initial.nextCursor });
  const retry = useRef<() => void>(() => {});
  const seed = useRef(initial);
  useEffect(() => {
    const element = strip.current;
    const lane = seed.current;
    if (!element || busy) return;
    const params = new URLSearchParams(query);
    const pages: Page[] = [{ cursor: params.get(cursorKey) ?? "", start: 0, count: lane.items.length, next: lane.nextCursor }];
    const cache = new Map<number, T[]>([[0, lane.items]]);
    let extent = lane.items.length;
    let active = true, failed = false;
    let pending: AbortController | undefined;
    let retryIndex = 0;
    let frame = 0;
    let center = 0;

    function publish() {
      const indices = [...cache.keys()].sort((a, b) => a - b);
      // The cache is contiguous during normal scrolling. A jump to an evicted
      // page replaces it, so spacers always represent exact server positions.
      const first = indices[0], last = indices.at(-1)!;
      setWindow({ items: indices.flatMap(index => cache.get(index)!), before: pages[first].start,
        after: extent - pages[last].start - pages[last].count, loading: !!pending, failed,
        complete: !pages.at(-1)!.next });
    }
    function load(index: number) {
      if (pending || !active || failed) return;
      const page = pages[index];
      const cursor = page?.cursor ?? pages.at(-1)!.next;
      const request = new URLSearchParams(query);
      if (cursor) request.set(cursorKey, cursor); else request.delete(cursorKey);
      const controller = new AbortController();
      pending = controller; retryIndex = index; publish();
      apiRequest<R>(`${endpoint}?${request}`, { signal: controller.signal }).then(response => {
        if (!active || controller.signal.aborted) return;
        const next = readPage(response);
        if (!next) throw new Error("Missing gallery entries");
        if (!page) {
          pages.push({ cursor, start: extent, count: next.items.length, next: next.items.length && next.nextCursor !== cursor ? next.nextCursor : "" });
          extent += next.items.length;
        }
        // A scrollbar jump may skip pages that have already left the cache.
        if (![...cache.keys()].some(key => Math.abs(key - index) <= 1)) cache.clear();
        cache.set(index, next.items);
        while (cache.size > 3) {
          const furthest = [...cache.keys()].sort((a, b) => Math.abs(b - center) - Math.abs(a - center))[0];
          cache.delete(furthest);
        }
        pending = undefined; publish();
        frame = requestAnimationFrame(check);
      }).catch(() => {
        if (!active || controller.signal.aborted) return;
        pending = undefined; failed = true; publish();
      });
    }
    function check() {
      if (!active || pending || failed) return;
      const card = element!.querySelector<HTMLElement>(".all-gallery-card");
      if (!card) return;
      const gap = parseFloat(getComputedStyle(element!).columnGap) || 0;
      const stride = card.getBoundingClientRect().width + gap;
      if (!stride) return;
      const first = Math.floor(element!.scrollLeft / stride);
      const last = Math.ceil((element!.scrollLeft + element!.clientWidth) / stride) - 1;
      center = Math.max(0, pages.findIndex(page => page.start + page.count > (first + last) / 2));
      const missing = pages.findIndex((page, index) => page.start <= last && page.start + page.count > first && !cache.has(index));
      if (missing >= 0) { load(missing); return; }
      if (last >= extent - 3 && pages.at(-1)!.next) load(pages.length);
    }
    function schedule() { cancelAnimationFrame(frame); frame = requestAnimationFrame(check); }
    retry.current = () => { failed = false; load(retryIndex); };
    element.addEventListener("scroll", schedule, { passive: true });
    const observer = new ResizeObserver(schedule);
    observer.observe(element);
    schedule();
    return () => { active = false; pending?.abort(); cancelAnimationFrame(frame); observer.disconnect(); element.removeEventListener("scroll", schedule); };
  // The gallery is keyed by the response's query, so a filter change starts a new
  // cursor history. Opening details and other parent renders retain this window.
  }, [query, busy, strip, endpoint, cursorKey, readPage]);
  return { ...window, retry: () => retry.current() };
}
