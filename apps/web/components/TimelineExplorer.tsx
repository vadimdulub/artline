"use client";
import { RecordDrawer } from "./RecordDrawer";
import { useEffect, useMemo, useRef, useState } from "react";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineFilterSuggestions } from "./TimelineFilterSuggestions";
import { AtlasFilters, ActiveFilters } from "./AtlasFilters";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { ArtworkFilterFields } from "./EntityFilterFields";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";
import { apiRequest, countryName, errorMessage } from "@/lib/api";
import { artworkYearPosition, artworkYearAtPosition, isCurrentPeriod, normalizeRange, positionArtists, visibleArtworkTicks, presetRange } from "@/lib/timeline";
import { popularPaintersOnly, womenArtistsOnly, queryValues, updateQuery, useQueryString } from "@/lib/url-state";
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
  const womenOnly = womenArtistsOnly(params);
  const painterChoices = usePainterChoices(painters, popularOnly, "", "", womenOnly);
  const slug = params.get("artist") ?? "";
  const [facets, setFacets] = useState<TimelineFacets>({ countries: [], movements: [], regions: [] });
  const [facetError, setFacetError] = useState(false);
  const [result, setResult] = useState<{ key: string; data?: TimelineResponse; error?: string }>({ key: "" });
  const [selected, setSelected] = useState<{ slug: string; data?: ArtistDetail; error?: string }>({ slug: "" });
  const [retry, setRetry] = useState(0);
  const [width, setWidth] = useState(1200);
  const stage = useRef<HTMLDivElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const requestParams = new URLSearchParams({ start: String(start), end: String(end), popular: String(popularOnly), women: String(womenOnly) });
  for (const [key, values] of Object.entries({ region: regions, country: countries, movement: selectedMovements, painter: painters, work_type: workTypes })) values.forEach(value => requestParams.append(key, value));
  if (query) requestParams.set("q", query);
  const requestKey = requestParams.toString();
  const loading = result.key !== requestKey;
  const data = result.data;
  const needsFilter = data?.mode === "density" && data.periods.length > 0 && data.periods.every(period => isCurrentPeriod(period, start, end));
  const suggestions = data?.suggested_filters ?? [];
  const error = result.key === requestKey ? result.error : undefined;
  const positioned = useMemo(() => positionArtists(data?.items ?? [], 1100, 2000, width), [data, width]);
  const laneCount = Math.max(4, ...positioned.map(item => item.lane + 1));
  const ticks = visibleArtworkTicks(1100, 2000, width);
  const rangeMarkers = [1400, 1500, 1600, 1700, 1800, 1900]
    .filter(year => (100 - artworkYearPosition(year)) * (width - 24) / 100 >= 60)
    .filter((_, index) => width >= 700 || index % 2 === 0)
    .map(year => ({ year, label: String(year) }));

  // Publication remains enforced by the server. Old bookmarks must not retain an
  // invisible editorial filter after its removal from the browsing interface.
  useEffect(() => { if (params.has("status")) updateQuery({ status: null }); }, [params]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest<TimelineFacets>(`timeline/facets?popular=${popularOnly}&women=${womenOnly}`, { signal: controller.signal }).then(data => { setFacets(data); setFacetError(false); }).catch(() => { if (!controller.signal.aborted) setFacetError(true); });
    return () => controller.abort();
  }, [retry, popularOnly, womenOnly]);

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

  function setRange(a: number, b: number) {
    const [from, to] = normalizeRange(String(a), String(b));
    updateQuery({ start: String(from), end: String(to) });
  }
  function focusSearch() {
    searchInput.current?.scrollIntoView({ block: "center" });
    searchInput.current?.focus({ preventScroll: true });
  }
  function selectPeriod(a: number, b: number) {
    if (isCurrentPeriod({ start_year: a, end_year: b }, start, end)) {
      if (suggestions[0]) applySuggestion(suggestions[0]);
      else focusSearch();
    }
    else setRange(a, b);
  }
  function applySuggestion(suggestion: NonNullable<TimelineResponse["suggested_filters"]>[number]) {
    updateQuery({ [suggestion.key]: suggestion.value }, true);
  }
  function reset() { updateQuery({ start: null, end: null, q: null, painter: null, country: null, movement: null, region: null, work_type: null, status: null, women: null, popular: null }, true); }
  function clearFilters() { updateQuery({ q: null, painter: null, region: null, movement: null, country: null, work_type: null, status: null, women: null, popular: "false" }, true); }
  function openArtist(artistSlug: string) { updateQuery({ artist: artistSlug, work: null, art_year: null, art_cursor: null }, true); }
  function closeArtist() { updateQuery({ artist: null, work: null, art_year: null, art_cursor: null }, true); }
  const movements = [...new Map((data?.items ?? []).map(item => [item.movement.slug, item.movement])).values()];
  const painterIndex = (data?.items ?? []).findIndex(item => item.slug === slug);

  const activeFilters = [
    { key: "q", value: query, label: `Search: ${query}` },
  ].filter(item => item.value).map(item => ({ ...item, remove: () => updateQuery({ [item.key]: null }, true) }));
  if (womenOnly) activeFilters.push({ key: "women", value: "true", label: "Women artists", remove: () => updateQuery({ women: null }, true) });
  if (popularOnly) activeFilters.push({ key: "popular", value: "true", label: "Top 100 painters", remove: () => updateQuery({ popular: "false" }, true) });
  for (const group of [{ key: "painter", values: painters, options: painterChoices.options }, { key: "movement", values: selectedMovements, options: facets.movements }, { key: "country", values: countries, options: facets.countries }, { key: "region", values: regions, options: facets.regions ?? [] }, { key: "work_type", values: workTypes, options: workTypeOptions }]) {
    for (const value of group.values) activeFilters.push({ key: `${group.key}-${value}`, value, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => updateQuery({ [group.key]: group.values.filter(item => item !== value) }, true) });
  }

  return <>
    <section className="explorer" aria-labelledby="timeline-title">
      {facetError && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <AtlasFilters searchRef={searchInput} query={query} onQuery={value => updateQuery({ q: value })} onReset={reset} placeholder="Painter, place, movement, or work" activeCount={activeFilters.filter(f => f.key !== "q").length}>
          <ArtworkFilterFields params={requestParams} change={values=>updateQuery(values,true)} facets={facets} painterChoices={painterChoices} unavailable={facetError} />
      </AtlasFilters>
      <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={searchInput} />
      <div className="timeline-dark artworks-compressed-scale">
        <div className="timeline-heading-row">
          <div><p className="range-caption">Selected years</p><h1 id="timeline-title" className="time-title"><span className="sr-only">Painting across time: </span>{start}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{end}</h1></div>
          <div className="timeline-heading-tools">
            <div className="timeline-counter" role="status">{loading ? "Finding painters…" : error ? "Connection interrupted" : `${data?.total ?? 0} ${data?.total === 1 ? "painter" : "painters"} in this view`}</div>
            {movements.length > 0 && <details className="movement-key"
              onKeyDown={event => { if (event.key === "Escape") { event.currentTarget.open = false; event.currentTarget.querySelector("summary")?.focus(); } }}
              onBlur={event => { if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false; }}>
              <summary>Movement colour key <span>{movements.length} in this view</span></summary>
              <div className="timeline-legend" aria-label="Movements in this view">{movements.map(item => <button key={item.slug} aria-pressed={selectedMovements.includes(item.slug)} onClick={() => updateQuery({ movement: selectedMovements.includes(item.slug) ? selectedMovements.filter(value => value !== item.slug) : [...selectedMovements, item.slug] }, true)}><i style={{ background: item.color }} />{item.name}</button>)}</div>
            </details>}
          </div>
        </div>
        <TimelineGrid stageRef={stage} busy={loading} selection={{ left: artworkYearPosition(start), right: artworkYearPosition(end) }} ticks={ticks.map(year => ({ key: year, label: String(year), position: artworkYearPosition(year) }))}>
          <div className="book-scale-break" style={{ left: `${artworkYearPosition(1400)}%` }} aria-hidden="true" />
          {error ? <div className="state-panel"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={() => { setResult({ key: "" }); setRetry(value => value + 1); }}>Try again</button></div> :
            data?.mode === "density" ? <><TimelineOverview key={`${start}-${end}`} periods={data.periods} start={start} end={end} position={year => artworkYearPosition(year)} disabled={loading} suggestion={suggestions[0]} onSelect={selectPeriod} /><TimelineFilterSuggestions suggestions={suggestions} noun="painters" needsFilter={Boolean(needsFilter)} disabled={loading} guidanceId="density-guidance" onApply={applySuggestion} onChooseFilters={focusSearch}>{!popularOnly && <button type="button" disabled={loading} onClick={() => updateQuery({ popular: null }, true)}>Show popular painters</button>}</TimelineFilterSuggestions></> :
            positioned.length ? <TimelineLanes key={`${popularOnly}-${womenOnly}`} label="Painter timeline lanes" descriptionId="timeline-scroll-help" loading={loading} height={laneCount * 54 + 12}>{positioned.map(artist => <TimelineMark key={artist.id} className="artist-mark" disabled={loading} selected={artist.slug === slug} left={artist.left} top={artist.lane * 54 + 8} width={artist.width} labelOffset={artist.labelOffset} labelWidth={artist.labelWidth} color={artist.movement.color} onSelect={() => openArtist(artist.slug)} label={`${artist.name}, ${artist.date_display}, ${artist.movement.name}, ${artist.countries.map(countryName).join(", ")}, ${artist.artwork_count} recorded works`} title={`${artist.movement.name} · ${artist.artwork_count} recorded works`} name={artist.name} date={artist.date_display} />)}</TimelineLanes> :
            <div className="state-panel"><h2>{loading ? "Opening the atlas…" : "No painters in this view"}</h2>{!loading && <><p>{activeFilters.length ? "No records match these filters in this date range." : start !== 1100 || end !== 2000 ? "No painter records overlap these years. Try a wider date range." : preview ? "Painter records will appear here as they are added." : "The first painter records are still being reviewed."}</p><div className="empty-view-actions">{activeFilters.length > 0 && <button onClick={() => { clearFilters(); searchInput.current?.focus(); }}>Remove filters</button>}{(start !== 1100 || end !== 2000) && <button onClick={() => setRange(1100, 2000)}>Show full date range</button>}</div></>}</div>}
        </TimelineGrid>
        {data?.mode === "individual" && positioned.length > 0 && <p className="timeline-scroll-help" id="timeline-scroll-help">Scroll within the chart for more painters, or narrow the years below. Lines show recorded life or activity intervals; artworks are dated separately.</p>}
      <TimelineRangeControls start={start} end={end} minimum={1100} maximum={2000} onChange={setRange}
        presets={[[900, "Full range"], [100, "Century"], [50, "50 years"], [25, "25 years"]].map(([years, label]) => { const [a, b] = presetRange(start, end, Number(years)); return { label: String(label), start: a, end: b, active: end - start === years }; })}
        scale={{ position: year => artworkYearPosition(year), yearAt: percent => artworkYearAtPosition(percent), markers: rangeMarkers }}
        endpoints={["1100", "2000"]} />
      </div>
    </section>
    <section className="results-section" aria-busy={loading}><div className="results-heading"><h2 id="painter-index-title">{data?.mode === "density" ? "Explore a period" : "Painter index"}</h2><p>{data?.mode === "density" ? needsFilter ? "This period is busy. Try the suggested filter, or choose your own above." : "Choose a period to explore. Busy periods may need a painter, movement or country filter." : "Choose a name for artworks, collections and sources. Work counts describe our catalogue, not a painter’s lifetime output."}</p></div>
      {error ? <p className="results-error">Results will return when the connection is restored. Use “Try again” above.</p> : data?.mode === "density" ? <ul className="density-results">{(data.periods ?? []).map(period => <li key={period.start_year}><button disabled={loading} onClick={() => selectPeriod(period.start_year, period.end_year)}>{period.start_year}–{period.end_year}<span>{period.count} {period.count === 1 ? "painter" : "painters"}{isCurrentPeriod(period, start, end) && (suggestions[0] ? ` · Try ${suggestions[0].name} · ${suggestions[0].count} painters →` : " · Choose filters →")}</span></button></li>)}</ul> :
        <div className="painter-index-scroll" role="region" aria-labelledby="painter-index-title" tabIndex={0}><ol className="artist-results">{(data?.items ?? []).map(artist => <li key={artist.id}><button disabled={loading} aria-pressed={artist.slug === slug} onClick={() => openArtist(artist.slug)}><span className="movement-dot" style={{ background: artist.movement.color }} /><span><strong>{artist.name}</strong><small>{artist.date_display} · {artist.countries.map(countryName).join(", ")}</small></span><span className={`result-coverage${artist.artwork_count === 0 ? " is-missing" : ""}`}>{artist.artwork_count ? `${artist.artwork_count} ${artist.artwork_count === 1 ? "work" : "works"}` : "Works to add"}</span></button></li>)}</ol></div>}
    </section>
    {slug && <RecordDrawer label="Painter details" closeLabel="Close painter details" recordKey={slug} close={closeArtist} fallbackFocusId="timeline-title"
      title={painterIndex >= 0 ? `Painter ${painterIndex + 1} of ${data?.total}` : "Painter record"}
      navigation={<nav className="painter-navigation" aria-label="Browse painters"><button type="button" aria-label="Previous painter" disabled={loading || painterIndex <= 0} onClick={() => openArtist(data!.items[painterIndex - 1].slug)}>←</button><button type="button" aria-label="Next painter" disabled={loading || painterIndex < 0 || painterIndex >= (data?.items.length ?? 0) - 1} onClick={() => openArtist(data!.items[painterIndex + 1].slug)}>→</button></nav>}>{selected.slug !== slug ? <p className="record-loading">Opening painter record…</p> : selected.error ? <div className="record-error"><h2>Painter unavailable</h2><p>{selected.error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : selected.data && <ArtistChronologyRecord key={selected.data.id} artist={selected.data} workId={params.get("work")} onSelectWork={id => updateQuery({ work: id })} />}</RecordDrawer>}
  </>;
}
