"use client";
import { lockBodyScroll } from "@/lib/modal-scroll";
import { useEffect, useMemo, useRef, useState } from "react";
import { DensityCanvas } from "./DensityCanvas";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { MultiSelectFilter } from "./MultiSelectFilter";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";
import { apiRequest, countryName, errorMessage } from "@/lib/api";
import { normalizeRange, positionArtists, timelineTicks, presetRange } from "@/lib/timeline";
import { popularPaintersOnly, queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, TimelineFacets, TimelineResponse } from "@/lib/types";

export function TimelineExplorer({ preview }: { preview: boolean }) {
  const search = useQueryString();
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const [start, end] = normalizeRange(params.get("start"), params.get("end"));
  const query = params.get("q") ?? "";
  const countries = queryValues(params, "country").map(value => value.toUpperCase());
  const selectedMovements = queryValues(params, "movement");
  const painters = queryValues(params, "painter");
  const regions = queryValues(params, "region");
  const workTypes = queryValues(params, "work_type");
  const popularOnly = popularPaintersOnly(params);
  const painterChoices = usePainterChoices(painters, popularOnly);
  const slug = params.get("artist") ?? "";
  const [facets, setFacets] = useState<TimelineFacets>({ countries: [], movements: [], regions: [] });
  const [facetError, setFacetError] = useState(false);
  const [result, setResult] = useState<{ key: string; data?: TimelineResponse; error?: string }>({ key: "" });
  const [selected, setSelected] = useState<{ slug: string; data?: ArtistDetail; error?: string }>({ slug: "" });
  const [retry, setRetry] = useState(0);
  const [width, setWidth] = useState(1200);
  const stage = useRef<HTMLDivElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const drawerOpen = Boolean(slug);
  const dialog = useRef<HTMLDialogElement>(null);
  const drag = useRef<{ x: number; start: number; end: number; width: number } | null>(null);
  const requestParams = new URLSearchParams({ start: String(start), end: String(end), popular: String(popularOnly) });
  for (const [key, values] of Object.entries({ region: regions, country: countries, movement: selectedMovements, painter: painters, work_type: workTypes })) values.forEach(value => requestParams.append(key, value));
  if (query) requestParams.set("q", query);
  const requestKey = requestParams.toString();
  const loading = result.key !== requestKey;
  const data = result.data;
  const error = result.key === requestKey ? result.error : undefined;
  const positioned = useMemo(() => positionArtists(data?.items ?? [], start, end, width), [data, start, end, width]);
  const laneCount = Math.max(4, ...positioned.map(item => item.lane + 1));
  const allTicks = timelineTicks(start, end);
  const ticks = allTicks.filter((_, index) => index % Math.max(1, Math.ceil(allTicks.length / Math.max(3, width / 65))) === 0);

  // Publication remains enforced by the server. Old bookmarks must not retain an
  // invisible editorial filter after its removal from the browsing interface.
  useEffect(() => { if (params.has("status")) updateQuery({ status: null }); }, [params]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest<TimelineFacets>(`timeline/facets?popular=${popularOnly}`, { signal: controller.signal }).then(data => { setFacets(data); setFacetError(false); }).catch(() => { if (!controller.signal.aborted) setFacetError(true); });
    return () => controller.abort();
  }, [retry, popularOnly]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<TimelineResponse>(`timeline?${requestKey}`, { signal: controller.signal })
        .then(data => setResult({ key: requestKey, data }))
        .catch(error => { if (!controller.signal.aborted) setResult({ key: requestKey, error: errorMessage(error) }); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [requestKey, retry]);

  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!slug) return;
    const controller = new AbortController();
    apiRequest<ArtistDetail>(`artists/${encodeURIComponent(slug)}`, { signal: controller.signal })
      .then(data => setSelected({ slug, data }))
      .catch(error => { if (!controller.signal.aborted) setSelected({ slug, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [slug, retry]);

  useEffect(() => {
    const element = dialog.current;
    if (!drawerOpen || !element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll();
    element.showModal();
    return () => { element.close(); unlock(); focused?.focus({ preventScroll: true }); };
  }, [drawerOpen]);

  useEffect(() => { dialog.current?.scrollTo({ top: 0, behavior: "instant" }); }, [slug]);
  useEffect(() => {
    function shortcut(event: KeyboardEvent) {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || document.querySelector("dialog[open]")) return;
      if (event.target instanceof Element && event.target.closest("input,textarea,select,[contenteditable]")) return;
      event.preventDefault(); searchInput.current?.focus();
    }
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);

  function setRange(a: number, b: number) {
    const [from, to] = normalizeRange(String(a), String(b));
    updateQuery({ start: String(from), end: String(to) });
  }
  function pan(delta: number) {
    const span = end - start;
    const a = Math.max(1100, Math.min(2000 - span, start + delta));
    setRange(a, a + span);
  }
  function reset() { updateQuery({ start: null, end: null, q: null, painter: null, country: null, movement: null, region: null, work_type: null, status: null, popular: null }, true); }
  function clearFilters() { updateQuery({ q: null, painter: null, region: null, movement: null, country: null, work_type: null, status: null, popular: "false" }, true); }
  function openArtist(artistSlug: string) { updateQuery({ artist: artistSlug, work: null, art_year: null, art_cursor: null }, true); }
  function closeArtist() { updateQuery({ artist: null, work: null, art_year: null, art_cursor: null }, true); }
  const movements = [...new Map((data?.items ?? []).map(item => [item.movement.slug, item.movement])).values()];
  const painterIndex = (data?.items ?? []).findIndex(item => item.slug === slug);

  const activeFilters = [
    { key: "q", value: query, label: `Search: ${query}` },
  ].filter(item => item.value).map(item => ({ ...item, remove: () => updateQuery({ [item.key]: null }, true) }));
  for (const group of [{ key: "painter", values: painters, options: painterChoices.options }, { key: "movement", values: selectedMovements, options: facets.movements }, { key: "country", values: countries, options: facets.countries }, { key: "region", values: regions, options: facets.regions ?? [] }, { key: "work_type", values: workTypes, options: workTypeOptions }]) {
    for (const value of group.values) activeFilters.push({ key: `${group.key}-${value}`, value, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => updateQuery({ [group.key]: group.values.filter(item => item !== value) }, true) });
  }

  return <>
    <section className="explorer" aria-labelledby="timeline-title">
      {facetError && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <div className="atlas-filter-system">
        <label className="search-field"><span>Search</span><input ref={searchInput} aria-keyshortcuts="/" type="search" placeholder="Painter, place, movement, or work" value={query} onChange={event => updateQuery({ q: event.target.value })} /><kbd aria-hidden="true">/</kbd></label>
        <button className="reset-button" onClick={reset}>Reset view</button>
        <div className="atlas-filter-row">
          <MultiSelectFilter label="Painters" allLabel="All painters" {...painterChoices} values={painters} onChange={values => updateQuery({ painter: values }, true)} helpText="Select painters together, for example Monet and Pissarro. Search here adds names; it does not replace your selection." />
          <MultiSelectFilter label="Movements" allLabel="All movements" options={facets.movements} values={selectedMovements} onChange={values => updateQuery({ movement: values }, true)} unavailable={facetError} />
          <MultiSelectFilter label="Regions" allLabel="All regions" options={facets.regions ?? []} values={regions} onChange={values => updateQuery({ region: values }, true)} unavailable={facetError} />
          <MultiSelectFilter label="Countries" allLabel="All countries" options={facets.countries} values={countries} onChange={values => updateQuery({ country: values }, true)} unavailable={facetError} />
          <MultiSelectFilter label="Work types" allLabel="All types" options={workTypeOptions} values={workTypes} onChange={values => updateQuery({ work_type: values }, true)} />
          <label className="popular-filter"><input type="checkbox" checked={popularOnly} onChange={event => updateQuery({ popular: event.target.checked ? null : "false" }, true)} /><span>Only popular painters</span></label>
        </div>
      </div>
      <p className="filter-combination-help"><span>Match any value within a filter; match all filter groups together.{(selectedMovements.length > 0 || countries.length > 0 || regions.length > 0) && " Filters use recorded classifications; painters with missing data may be excluded."}</span><a href="/about#popular-painters">About the selection</a></p>
      {activeFilters.length > 0 && <div className="active-filters" aria-label="Active filters"><span>Filtered by</span>{activeFilters.map(filter => <button key={filter.key} type="button" aria-label={`Remove ${filter.label} filter`} onClick={() => { filter.remove(); searchInput.current?.focus(); }}>{filter.label}<span aria-hidden="true">×</span></button>)}<button className="clear-filters" type="button" onClick={() => { clearFilters(); searchInput.current?.focus(); }}>Clear filters</button></div>}
      <div className="timeline-dark">
        <div className="timeline-heading-row"><div><p className="range-caption">Visible range</p><h1 id="timeline-title" className="time-title"><span className="sr-only">Painting across time: </span>{start}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{end}</h1></div><div className="timeline-counter" role="status">{loading ? "Finding painters…" : error ? "Connection interrupted" : `${data?.total ?? 0} ${data?.total === 1 ? "painter" : "painters"} in this view`}<small>{preview ? "Research preview · records may be incomplete" : "Published catalogue"}</small></div></div>
        <div className="timeline-stage" ref={stage} aria-busy={loading}>
          <div className="tick-row" aria-hidden="true">{ticks.map(year => <span key={year} style={{ left: `${((year - start) / Math.max(1, end - start)) * 100}%` }}><i />{year}</span>)}</div>
          {error ? <div className="state-panel"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={() => { setResult({ key: "" }); setRetry(value => value + 1); }}>Try again</button></div> :
            data?.mode === "density" ? <><DensityCanvas bins={data.bins} start={start} end={end} /><div className="density-help"><p>Painters grouped by the midpoint of their recorded life or activity dates. Choose a period below to explore.</p><button disabled={loading} onClick={() => { const [a, b] = presetRange(start, end, 100); setRange(a, b); }}>Zoom into a century</button></div></> :
            positioned.length ? <div className="timeline-lanes" key={`${start}-${end}-${popularOnly}`} role="region" aria-label="Painter timeline lanes" aria-describedby="timeline-scroll-help" tabIndex={0}><div className={loading ? "artist-field is-loading" : "artist-field"} style={{ height: `${laneCount * 54 + 12}px` }}>{positioned.map(artist => <button key={artist.id} className="artist-mark" disabled={loading} aria-pressed={artist.slug === slug} style={{ left: `${artist.left}%`, top: `${artist.lane * 54 + 8}px`, width: `${artist.width}%`, ["--movement-color" as string]: artist.movement.color, ["--label-offset" as string]: `${artist.labelOffset}px`, ["--label-width" as string]: `${artist.labelWidth}px` }} onClick={() => openArtist(artist.slug)} aria-label={`${artist.name}, ${artist.date_display}, ${artist.movement.name}, ${artist.countries.map(countryName).join(", ")}, ${artist.artwork_count} recorded works`} title={`${artist.movement.name} · ${artist.artwork_count} recorded works`}><span>{artist.name}</span><small>{artist.date_display}</small><i /></button>)}</div></div> :
            <div className="state-panel"><h2>{loading ? "Opening the atlas…" : "No painters in this view"}</h2>{!loading && <><p>{activeFilters.length ? "No records match these filters in this date range." : start !== 1100 || end !== 2000 ? "No painter records overlap these years. Try a wider date range." : preview ? "Painter records will appear here as they are added." : "The first painter records are still being reviewed."}</p><div className="empty-view-actions">{activeFilters.length > 0 && <button onClick={() => { clearFilters(); searchInput.current?.focus(); }}>Remove filters</button>}{(start !== 1100 || end !== 2000) && <button onClick={() => setRange(1100, 2000)}>Show full date range</button>}</div></>}</div>}
        </div>
        {data?.mode === "individual" && positioned.length > 0 && <p className="timeline-scroll-help" id="timeline-scroll-help">Scroll within the chart for more painters, or narrow the years below. Lines show recorded life or activity intervals; artworks are dated separately.</p>}
      <section className="timeline-focus" aria-labelledby="focus-title">
      <div className="range-toolbar">
        <h2 id="focus-title">Focus the timeline</h2>
        <div className="preset-group" aria-label="Timeline range presets">{[[900, "Full range"], [100, "Century"], [50, "50 years"], [25, "25 years"]].map(([years, label]) => <button key={years} aria-pressed={end - start === years} onClick={() => { const [a, b] = presetRange(start, end, Number(years)); setRange(a, b); }}>{label}</button>)}</div>
        <div className="year-inputs"><label><span>From</span><input aria-label="Start year" key={`start-${start}`} type="number" step={1} defaultValue={start} min={1100} max={end - 1} onBlur={event => { const value = Math.max(1100, Math.min(end - 1, Math.round(Number(event.target.value) || start))); event.target.value = String(value); setRange(value, end); }} onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); }} /></label><label><span>To</span><input aria-label="End year" key={`end-${end}`} type="number" step={1} defaultValue={end} min={start + 1} max={2000} onBlur={event => { const value = Math.min(2000, Math.max(start + 1, Math.round(Number(event.target.value) || end))); event.target.value = String(value); setRange(start, value); }} onKeyDown={event => { if (event.key === "Enter") event.currentTarget.blur(); }} /></label></div>
      </div>
      <div className="range-track">
        <button className="range-window" aria-label="Move selected time range" style={{ left: `${(start - 1100) / 9}%`, width: `${(end - start) / 9}%` }} onPointerDown={event => { event.currentTarget.setPointerCapture(event.pointerId); drag.current = { x: event.clientX, start, end, width: event.currentTarget.parentElement!.clientWidth }; }} onPointerMove={event => { if (!drag.current) return; const d = drag.current; const offset = Math.round((event.clientX - d.x) / d.width * 900); const a = Math.max(1100, Math.min(2000 - (d.end - d.start), d.start + offset)); setRange(a, a + d.end - d.start); }} onPointerUp={() => { drag.current = null; }} onPointerCancel={() => { drag.current = null; }} onKeyDown={event => { if (event.key === "ArrowLeft" || event.key === "ArrowRight") { event.preventDefault(); pan(event.key === "ArrowLeft" ? -10 : 10); } }}><span>Drag to move the range</span></button>
        <input aria-label="Timeline start handle" aria-valuemax={end - 1} type="range" min={1100} max={2000} value={start} onChange={event => setRange(Math.min(Number(event.target.value), end - 1), end)} />
        <input aria-label="Timeline end handle" aria-valuemin={start + 1} type="range" min={1100} max={2000} value={end} onChange={event => setRange(start, Math.max(Number(event.target.value), start + 1))} />
      </div>
      <div className="range-endpoints" aria-hidden="true">{["XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"].map(century => <span key={century}>{century}</span>)}</div>
      <div className="range-pan"><button type="button" aria-label="Move range 10 years earlier" disabled={start === 1100} onClick={() => pan(-10)}>← Earlier</button><span>Move the range · 10 years</span><button type="button" aria-label="Move range 10 years later" disabled={end === 2000} onClick={() => pan(10)}>Later →</button></div>
      </section>
      {movements.length > 0 && <details className="movement-key"><summary>Movement colour key <span>{movements.length} in this view</span></summary><div className="timeline-legend" aria-label="Movements in this view">{movements.map(item => <button key={item.slug} aria-pressed={selectedMovements.includes(item.slug)} onClick={() => updateQuery({ movement: selectedMovements.includes(item.slug) ? selectedMovements.filter(value => value !== item.slug) : [...selectedMovements, item.slug] }, true)}><i style={{ background: item.color }} />{item.name}</button>)}</div></details>}
      </div>
    </section>
    <section className="results-section" aria-busy={loading}><div className="results-heading"><h2 id="painter-index-title">{data?.mode === "density" ? "Explore a period" : "Painter index"}</h2><p>{data?.mode === "density" ? "Choose a period to reveal individual painters." : "Choose a name for artworks, collections and sources. Work counts describe our catalogue, not a painter’s lifetime output."}</p></div>
      {error ? <p className="results-error">Results will return when the connection is restored. Use “Try again” above.</p> : data?.mode === "density" ? <ul className="density-results">{(data.periods ?? []).map(period => <li key={period.start_year}><button disabled={loading} onClick={() => setRange(period.start_year, Math.max(period.start_year + 1, period.end_year))}>{period.start_year}–{period.end_year}<span>{period.count} {period.count === 1 ? "painter" : "painters"}</span></button></li>)}</ul> :
        <div className="painter-index-scroll" role="region" aria-labelledby="painter-index-title" tabIndex={0}><ol className="artist-results">{(data?.items ?? []).map(artist => <li key={artist.id}><button disabled={loading} aria-pressed={artist.slug === slug} onClick={() => openArtist(artist.slug)}><span className="movement-dot" style={{ background: artist.movement.color }} /><span><strong>{artist.name}</strong><small>{artist.date_display} · {artist.countries.map(countryName).join(", ")}</small></span><span className={`result-coverage${artist.artwork_count === 0 ? " is-missing" : ""}`}>{artist.artwork_count ? `${artist.artwork_count} ${artist.artwork_count === 1 ? "work" : "works"}` : "Works to add"}</span></button></li>)}</ol></div>}
    </section>
    {slug && <dialog className="painter-dialog" ref={dialog} aria-label="Painter details" onCancel={event => { event.preventDefault(); closeArtist(); }} onClick={event => { if (event.target === event.currentTarget) { const bounds = event.currentTarget.getBoundingClientRect(); if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) closeArtist(); } }}><div className="dialog-toolbar"><span>{painterIndex >= 0 ? `Painter ${painterIndex + 1} of ${data?.total}` : "Painter record"}</span><nav className="painter-navigation" aria-label="Browse painters"><button type="button" aria-label="Previous painter" disabled={loading || painterIndex <= 0} onClick={() => openArtist(data!.items[painterIndex - 1].slug)}>←</button><button type="button" aria-label="Next painter" disabled={loading || painterIndex < 0 || painterIndex >= (data?.items.length ?? 0) - 1} onClick={() => openArtist(data!.items[painterIndex + 1].slug)}>→</button></nav><button className="close-painter" autoFocus type="button" onClick={closeArtist} aria-label="Close painter details"><span aria-hidden="true">×</span></button></div>{selected.slug !== slug ? <p className="record-loading">Opening painter record…</p> : selected.error ? <div className="record-error"><h2>Painter unavailable</h2><p>{selected.error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : selected.data && <ArtistChronologyRecord key={selected.data.id} artist={selected.data} workId={params.get("work")} onSelectWork={id => updateQuery({ work: id })} />}</dialog>}
  </>;
}
