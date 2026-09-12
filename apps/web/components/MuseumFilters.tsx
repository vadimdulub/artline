"use client";
import { useRef } from "react";
import { updateQuery } from "@/lib/url-state";
import styles from "./Museums.module.css";

export function setMuseumFilters(values: Record<string, string | string[] | null>) { updateQuery({ ...values, cursor: null }, !Object.keys(values).some(key => ["q", "start", "end"].includes(key))); }
export function MuseumChips({ filters, clear }: { filters: { key: string; label: string; remove: () => void }[]; clear: () => void }) {
  const container = useRef<HTMLDivElement>(null);
  function restoreFocus() { container.current?.closest("main")?.querySelector<HTMLInputElement>("input[type=search]")?.focus(); }
  return filters.length > 0 ? <div className={styles.chips} ref={container} aria-label="Active museum filters"><span>Filtered by</span>{filters.map(filter => <button type="button" key={filter.key} aria-label={`Remove ${filter.label} filter`} onClick={() => { filter.remove(); restoreFocus(); }}>{filter.label}<span aria-hidden="true"> ×</span></button>)}<button type="button" onClick={() => { clear(); restoreFocus(); }}>Clear filters</button></div> : null;
}
export function MuseumPagination({ next, cursor }: { next: string; cursor: string | null }) {
  return next || cursor ? <nav className={styles.pagination} aria-label="Museum catalogue pages">{cursor && <button onClick={() => updateQuery({ cursor: null }, true)}>First page</button>}{next && <button onClick={() => { updateQuery({ cursor: next }, true); document.getElementById("museum-results-title")?.focus(); }}>Next page</button>}</nav> : null;
}
export function MuseumError({ message, retry }: { message: string; retry: () => void }) {
  return <div className={styles.empty} role="alert"><h2>We couldn’t load this view</h2><p>{message}</p><button onClick={retry}>Try again</button><button onClick={() => setMuseumFilters({ q: null, region: null, country: null, selection: null, display: null, artist: null, movement: null, venue: null, start: null, end: null, unknown_date: null, work_type: null, image_only: null, sort: null })}>Reset filters and page</button></div>;
}
