"use client";

import { useEffect, useRef, useState } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { EventsFacets, EventsResponse } from "@/lib/events";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { AtlasFilters, ActiveFilters } from "./AtlasFilters";
import { EventFilterFields, eventDimensions } from "./EntityFilterFields";
import { EventsTimeline } from "./EventsTimeline";
import { EventDrawer } from "./EventDrawer";
import styles from "./Books.module.css";

const cleared = { q: null, topic: null, kind: null, country: null, region: null, top100: "false" };

export function EventsIndex() {
  const queryString = useQueryString();
  const params = new URLSearchParams(queryString);
  if (!params.has("top100")) params.set("top100", "true");
  const top100 = params.get("top100") === "true";
  const query = params.get("q") ?? "";
  const selected = params.get("event") ?? "";
  const requestKey = new URLSearchParams([...params].filter(([key]) => ["q", "topic", "kind", "region", "country", "start", "end", "after", "top100"].includes(key))).toString();
  const [result, setResult] = useState<{ key: string; data?: EventsResponse; error?: string }>();
  const [facets, setFacets] = useState<{ data?: EventsFacets; error?: string }>();
  const [retry, setRetry] = useState(0);
  const search = useRef<HTMLInputElement>(null);
  const current = result?.key === requestKey;
  const data = current && !result?.error ? result?.data : undefined;
  const error = current ? result?.error : undefined;
  const loading = !current;
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<EventsResponse>(`events?${requestKey}`, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setResult({ key: requestKey, data }); })
        .catch(error => { if (!controller.signal.aborted) setResult(previous => ({ key: requestKey, data: previous?.data, error: errorMessage(error) })); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [requestKey, retry]);
  useEffect(() => {
    const controller = new AbortController();
    apiRequest<EventsFacets>(`events/facets?top100=${top100}`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setFacets({ data }); })
      .catch(error => { if (!controller.signal.aborted) setFacets(previous => ({ ...previous, error: errorMessage(error) })); });
    return () => controller.abort();
  }, [top100, retry]);
  function change(values: Record<string, string | string[] | null>, push = true) { updateQuery({ ...values, after: null }, push); }
  function reset() { change({ ...cleared, top100: null, start: null, end: null, event: null }); search.current?.focus(); }
  function page(after: string | null) { updateQuery({ after }, true); const heading = document.getElementById("event-index"); heading?.scrollIntoView({ block: "start" }); heading?.focus({ preventScroll: true }); }
  const choices = eventDimensions.map(d => ({ ...d, values: [...new Set(params.getAll(d.key))] }));
  const active = [
    ...(query ? [{ key: "q", label: `Search: ${query}`, remove: () => change({ q: null }) }] : []),
    ...(top100 ? [{ key: "top100", label: "Top 100 events", remove: () => change({ top100: "false" }) }] : []),
    ...choices.flatMap(d => d.values.map(value => ({ key: `${d.key}-${value}`, label: value, remove: () => change({ [d.key]: d.values.filter(item => item !== value) }) }))),
  ];
  const bounds = result?.data?.bounds ?? { start: -12000, end: 2000 };
  const year = (key: string, fallback: number) => { const raw = params.get(key); return raw && Number.isFinite(Number(raw)) ? Number(raw) : fallback; };
  const range = { start: year("start", bounds.start), end: year("end", bounds.end) };
  return <div className={styles.page}>
    <section className="explorer books-explorer" aria-labelledby="events-timeline">
      {facets?.error && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <AtlasFilters searchRef={search} query={query} onQuery={value => change({ q: value }, false)} onReset={reset} searchLabel="Find an event" placeholder="Event, place, or idea" columns={4} activeCount={active.filter(f => f.key !== "q").length}>
        <EventFilterFields params={params} change={change} facets={facets?.data} unavailable={Boolean(facets?.error)} />
      </AtlasFilters>
      <ActiveFilters filters={active} onClear={() => change(cleared)} searchRef={search} />
      <EventsTimeline data={data} metadata={result?.data} range={range} loading={loading} error={error} selected={selected} onSelect={event => updateQuery({ event }, true)}
        onRange={(start, end) => change({ start: String(start), end: String(end) }, false)} onRetry={() => setRetry(value => value + 1)} onReset={reset}
        onSuggestion={s => change({ [s.key]: s.value })} onTop100={() => change({ top100: null })} />
    </section>
    <section className={styles.shelf} aria-labelledby="event-index" aria-busy={loading}>
      <div className={styles.shelfHeader}><div><h2 id="event-index" tabIndex={-1}>Event index</h2><p>Explore the events, empires, and movements that connect art, literature, belief, science, and everyday life. World history through 2000.</p></div><p className={styles.count} role="status">{data ? `${data.total.toLocaleString("en-GB")} of ${data.selectionTotal.toLocaleString("en-GB")} events` : ""}</p></div>
      <ul className={styles.bookIndex} aria-label="Event index">{data?.items.map(event => <li key={event.id} data-selected={selected === event.id}><button type="button" aria-label={`Open ${event.title}`} aria-haspopup="dialog" onClick={() => updateQuery({ event: event.id }, true)}><strong>{event.title}</strong><span>{event.kind} · {event.topics.join(" · ")}</span><time>{event.years}</time></button></li>)}</ul>
      {data && (data.hasMore || params.has("after")) && <nav className={styles.pagination} aria-label="Event pages">{params.has("after") && <button onClick={() => page(null)}>First page</button>}<span>{data.items.length} events on this page</span>{data.hasMore && <button onClick={() => page(data.nextCursor)}>Next events</button>}</nav>}
      <p className={styles.footerNote}>The Top 100 offers starting points for exploration. The wider source-linked collection is under review; documentation coverage is not a definitive measure of historical importance. Uncertain dates and missing details remain visible.</p>
    </section>
    {selected && <EventDrawer id={selected} close={() => updateQuery({ event: null })} />}
  </div>;
}
