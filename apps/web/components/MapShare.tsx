"use client";
import { useEffect, useRef, useState } from "react";
import { useQueryString } from "@/lib/url-state";

export function MapShare({ compact = false }: { compact?: boolean }) {
  const query = useQueryString(), field = useRef<HTMLInputElement>(null), container = useRef<HTMLDivElement>(null), button = useRef<HTMLButtonElement>(null);
  const [result, setResult] = useState<{ query: string; url: string; copied: boolean }>();
  const current = result?.query === query ? result : undefined;
  useEffect(() => { if (current && !current.copied) { field.current?.focus(); field.current?.select(); } }, [current]);
  useEffect(() => {
    if (!current || current.copied) return;
    function dismiss(event: PointerEvent) { if (event.target instanceof Node && !container.current?.contains(event.target)) setResult(undefined); }
    document.addEventListener("pointerdown", dismiss, true);
    return () => document.removeEventListener("pointerdown", dismiss, true);
  }, [current]);
  async function copy() {
    const url = new URL(window.location.href);
    for (const name of ["painting", "artist", "book", "event"]) url.searchParams.delete(name);
    url.hash = "";
    try { await navigator.clipboard.writeText(url.href); setResult({ query, url: url.href, copied: true }); }
    catch { setResult({ query, url: url.href, copied: false }); }
  }
  const label = current?.copied ? "Link copied" : "Copy map link";
  return <div ref={container} className={`map-share${compact ? " is-compact" : ""}`} onKeyDown={event => { if (event.key === "Escape" && current && !current.copied) { event.preventDefault(); event.stopPropagation(); setResult(undefined); button.current?.focus(); } }}><button ref={button} type="button" aria-label={label} title={label} onClick={copy}><svg viewBox="0 0 24 24" aria-hidden="true"><path d={current?.copied ? "m5 12 4 4L19 6" : "m9 15 6-6m-7 3-2 2a4 4 0 0 0 6 6l2-2m-4-12 2-2a4 4 0 0 1 6 6l-2 2"} /></svg>{!compact && label}</button><span className="sr-only" role="status">{current?.copied ? "Map link copied." : current ? "Copy the selected link." : ""}</span>{current && !current.copied && <label className="map-share-fallback">Copy this map link<input ref={field} readOnly value={current.url} onFocus={event => event.currentTarget.select()} /></label>}</div>;
}
