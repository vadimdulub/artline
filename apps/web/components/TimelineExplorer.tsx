"use client";
import { BookmarkButton } from "./Bookmarks";
import { ExplorerFrame } from "./ExplorerFrame";
import { useFitYears } from "./use-fit-years";
import { timelineRequestKey } from "@/lib/timeline-request";
import { discoveryChanges } from "@/lib/discovery";

import { PainterPaintings } from "./PainterPaintings";
import "./PainterPaintings.css";
import { RecordDrawer } from "./RecordDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import { useEffect, useMemo, useRef, useState } from "react";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineFilterSuggestions } from "./TimelineFilterSuggestions";
import { AtlasFilters, ActiveFilters, focusAtlasSearch } from "./AtlasFilters";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineZoomOut } from "./TimelineZoomOut";
import { TimelineHeader } from "./TimelineHeader";
import { TimelinePopover } from "./TimelinePopover";
import { ArtistChronologyRecord } from "./ArtistChronologyRecord";
import { ArtworkFilterFields } from "./EntityFilterFields";
import { usePainterChoices, workTypeOptions } from "./use-painter-choices";
import { apiRequest, countryName, errorMessage } from "@/lib/api";
import { artworkYearPosition, artworkYearAtPosition, isCurrentPeriod, normalizeRange, positionArtists, visibleArtworkTicks } from "@/lib/timeline";
import { atlasTimelineScale } from "@/lib/atlas-timeline";
import { popularPaintersOnly, womenArtistsOnly, queryValues, updateQuery, useQueryString } from "@/lib/url-state";
import type { ArtistDetail, TimelineFacets, TimelineResponse } from "@/lib/types";

export function TimelineExplorer() {
  const search = useQueryString();
  const params = useMemo(() => new URLSearchParams(search), [search]);
  const paintings = params.get("view") === "paintings";
  const [start, end] = normalizeRange(params.get("start"), params.get("end"));
  const [rangePreview, setRangePreview] = useState<{ start: number; end: number } | null>(null);
  const [showMovementKeyOnEntry, setShowMovementKeyOnEntry] = useState(false);
  const displayRange = rangePreview ?? { start, end };
  const query = params.get("q") ?? "";
  const countries = queryValues(params, "country").map(value => value.toUpperCase());
  const selectedMovements = queryValues(params, "movement");
  const painters = queryValues(params, "painter");
  const regions = queryValues(params, "region");
  const workTypes = queryValues(params, "work_type");
  const popularOnly = popularPaintersOnly(params);
  const womenOnly = womenArtistsOnly(params);
  const painterChoices = usePainterChoices(painters, false, "", womenOnly);
  const slug = params.get("artist") ?? "";
  const [facets, setFacets] = useState<TimelineFacets>({ countries: [], movements: [], regions: [] });
  const [facetError, setFacetError] = useState(false);
  const [result, setResult] = useState<{ key: string; data?: TimelineResponse; error?: string }>({ key: "" });
  const [selected, setSelected] = useState<{ slug: string; data?: ArtistDetail; error?: string }>({ slug: "" });
  const [retry, setRetry] = useState(0);
  const [width, setWidth] = useState(1200);
  const stage = useRef<HTMLDivElement>(null);
  const searchInput = useRef<HTMLInputElement>(null);
  const viewSwitchRef = useRef<HTMLDivElement>(null);
  const restoreViewFocus = useRef(false);
  const requestParams = new URLSearchParams({ start: String(start), end: String(end), popular: String(popularOnly), women: String(womenOnly) });
  for (const [key, values] of Object.entries({ region: regions, country: countries, movement: selectedMovements, painter: painters, work_type: workTypes })) values.forEach(value => requestParams.append(key, value));
  if (query) requestParams.set("q", query);
  const requestKey = timelineRequestKey(requestParams);
  const loading = result.key !== requestKey;
  const data = result.data?.range.start === start && result.data.range.end === end ? result.data : undefined;
  useFitYears(!paintings && params.get("fit") === "true", !loading && !result.error, data?.matchedRange);
  const needsFilter = data?.mode === "density" && data.periods.length > 0 && data.periods.every(period => isCurrentPeriod(period, start, end));
  const suggestions = data?.suggested_filters ?? [];
  const error = result.key === requestKey ? result.error : undefined;
  const { focused, position, ticks } = useMemo(() => atlasTimelineScale({ start, end }, { start: 1100, end: 2000 }, width, {
    position: year => artworkYearPosition(year),
    ticks: visibleArtworkTicks(1100, 2000, width).map(year => ({ year, label: String(year) })),
  }), [start, end, width]);
  const positioned = useMemo(() => positionArtists(data?.items ?? [], start, end, width, position), [data, start, end, width, position]);
  const laneCount = Math.max(4, ...positioned.map(item => item.lane + 1));
  const rangeMarkers = [1400, 1500, 1600, 1700, 1800, 1900]
    .filter(year => (100 - artworkYearPosition(year)) * (width - 24) / 100 >= 60)
    .filter((_, index) => width >= 700 || index % 2 === 0)
    .map(year => ({ year, label: String(year) }));

  // Publication remains enforced by the server. Old bookmarks must not retain an
  // invisible editorial filter after its removal from the browsing interface.
  useEffect(() => { if (params.has("status")) updateQuery({ status: null }); }, [params]);

  useEffect(() => {
    if (!restoreViewFocus.current) return;
    viewSwitchRef.current?.querySelector<HTMLButtonElement>('[aria-pressed="true"]')?.focus({ preventScroll: true });
    restoreViewFocus.current = false;
  }, [paintings]);

  useEffect(() => {
    const controller = new AbortController();
    apiRequest<TimelineFacets>(`timeline/facets?popular=false&women=${womenOnly}`, { signal: controller.signal }).then(data => { setFacets(data); setFacetError(false); }).catch(() => { if (!controller.signal.aborted) setFacetError(true); });
    return () => controller.abort();
  }, [retry, womenOnly]);

  useEffect(() => {
    if (paintings) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      apiRequest<TimelineResponse>(`timeline?${requestKey}`, { signal: controller.signal })
        .then(data => { if (!controller.signal.aborted) setResult({ key: requestKey, data }); })
        .catch(error => { if (!controller.signal.aborted) setResult({ key: requestKey, error: errorMessage(error) }); });
    }, 160);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [requestKey, retry, paintings]);

  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, [paintings]);

  useEffect(() => {
    if (!slug || paintings) return;
    const controller = new AbortController();
    apiRequest<ArtistDetail>(`artists/${encodeURIComponent(slug)}`, { signal: controller.signal })
      .then(data => setSelected({ slug, data }))
      .catch(error => { if (!controller.signal.aborted) setSelected({ slug, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [slug, retry, paintings]);

  function change(values: Record<string, string | string[] | null>, push = false) { setRangePreview(null); updateQuery({ painting_after: null, painting: null, fit: null, ...discoveryChanges(values, "popular") }, push); }
  function changeView(showPaintings: boolean) {
    if (showPaintings === paintings) return;
    setShowMovementKeyOnEntry(true);
    restoreViewFocus.current = true;
    change({ view: showPaintings ? "paintings" : null, artist: null }, true);
  }
  function setRange(a: number, b: number) {
    const [from, to] = normalizeRange(String(a), String(b));
    change({ start: String(from), end: String(to) });
  }
  function focusSearch() {
    focusAtlasSearch(searchInput.current);
  }
  function selectPeriod(a: number, b: number) {
    if (isCurrentPeriod({ start_year: a, end_year: b }, start, end)) {
      if (suggestions[0]) applySuggestion(suggestions[0]);
      else focusSearch();
    }
    else change({ start: String(a), end: String(b), popular: "false", fit: "true" }, true);
  }
  function applySuggestion(suggestion: NonNullable<TimelineResponse["suggested_filters"]>[number]) {
    // Suggestions are counted within the current years and filters; do not refit.
    setRangePreview(null);
    updateQuery({ [suggestion.key]: suggestion.value, painting_after: null, painting: null, fit: null }, true);
  }
  function reset() { change({ start: null, end: null, q: null, painter: null, country: null, movement: null, region: null, work_type: null, status: null, women: null, popular: null, painting_highlights: null }, true); }
  function clearFilters() { change({ q: null, painter: null, region: null, movement: null, country: null, work_type: null, status: null, women: null, popular: "false" }, true); }
  function openArtist(artistSlug: string) { change({ artist: artistSlug, work: null, art_year: null, art_cursor: null }, true); }
  function closeArtist() { change({ artist: null, work: null, art_year: null, art_cursor: null }, true); }
  const movements = [...new Map((data?.items ?? []).map(item => [item.movement.slug, item.movement])).values()];
  const painterIndex = (data?.items ?? []).findIndex(item => item.slug === slug);
  const viewSwitch = <div ref={viewSwitchRef} className="painter-view-switch" role="group" aria-label="Painter view"><button type="button" aria-pressed={!paintings} onClick={() => changeView(false)}>Painter lifespans</button><button type="button" aria-pressed={paintings} onClick={() => changeView(true)}>Paintings</button></div>;

  const activeFilters = [
    { key: "q", value: query, label: `Search: ${query}` },
  ].filter(item => item.value).map(item => ({ ...item, remove: () => change({ [item.key]: null }, true) }));
  if (womenOnly) activeFilters.push({ key: "women", value: "true", label: "Women artists", remove: () => change({ women: null }, true) });
  if (popularOnly) activeFilters.push({ key: "popular", value: "true", label: "Top 100 painters", remove: () => change({ popular: "false" }, true) });
  for (const group of [{ key: "painter", values: painters, options: painterChoices.options }, { key: "movement", values: selectedMovements, options: facets.movements }, { key: "country", values: countries, options: facets.countries }, { key: "region", values: regions, options: facets.regions ?? [] }, { key: "work_type", values: workTypes, options: workTypeOptions }]) {
    for (const value of group.values) activeFilters.push({ key: `${group.key}-${value}`, value, label: group.options.find(item => item.slug === value)?.name ?? value.replaceAll("-", " "), remove: () => change({ [group.key]: group.values.filter(item => item !== value) }, true) });
  }

  return <>
    <ExplorerFrame className="explorer" aria-labelledby="timeline-title">
      {facetError && <p className="save-message" role="status">Some filter choices could not be loaded. <button onClick={() => setRetry(value => value + 1)}>Retry filters</button></p>}
      <AtlasFilters searchRef={searchInput} query={query} onQuery={value => change({ q: value })} onReset={reset} placeholder="Painter, place, movement, or work" activeCount={activeFilters.filter(f => f.key !== "q").length}>
          <ArtworkFilterFields params={requestParams} change={values=>change(values,true)} facets={facets} painterChoices={painterChoices} unavailable={facetError} />
      </AtlasFilters>
      <ActiveFilters filters={activeFilters} onClear={clearFilters} searchRef={searchInput} />
      {paintings ? <PainterPaintings filters={requestKey} start={start} end={end} setRange={setRange} onPeriod={(a,b)=>change({start:String(a),end:String(b),popular:"false",fit:"true"},true)} viewSwitch={viewSwitch} /> : <div className={`timeline-dark${focused ? "" : " artworks-compressed-scale"}`}>
        <TimelineHeader className="painter-lifespan-heading" controls={viewSwitch}
          status={loading ? "Finding painters…" : error ? "Connection interrupted" : `${data?.total ?? 0} ${data?.total === 1 ? "painter" : "painters"} in this view`}
          zoom={<TimelineZoomOut disabled={!focused} onClick={() => change({ start: null, end: null }, true)} />}>
          <h1 id="timeline-title" className="time-title"><span className="sr-only">Painter lifespans: </span>{displayRange.start}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{displayRange.end}</h1>
          {movements.length > 0 && <TimelinePopover label="Movement colour key" className="movement-key" defaultOpen={showMovementKeyOnEntry}><div className="timeline-legend" aria-label="Movements in this view">{movements.map(item => <button key={item.slug} aria-pressed={selectedMovements.includes(item.slug)} onClick={() => change({ movement: selectedMovements.includes(item.slug) ? selectedMovements.filter(value => value !== item.slug) : [...selectedMovements, item.slug] }, true)}><i style={{ background: item.color }} />{item.name}</button>)}</div></TimelinePopover>}
        </TimelineHeader>
        <TimelineGrid stageRef={stage} busy={loading} ticks={ticks.map(tick => ({ key: tick.year, label: tick.label, position: position(tick.year) }))}>
          {!focused && <div className="book-scale-break" style={{ left: `${artworkYearPosition(1400)}%` }} aria-hidden="true" />}
          {error ? <div className="state-panel"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={() => { setResult({ key: "" }); setRetry(value => value + 1); }}>Try again</button></div> :
            data?.mode === "density" ? <><TimelineOverview key={`${start}-${end}`} periods={data.periods} start={start} end={end} position={position} disabled={loading} suggestion={suggestions[0]} onSelect={selectPeriod} /><TimelineFilterSuggestions suggestions={suggestions} noun="painters" needsFilter={Boolean(needsFilter)} disabled={loading} guidanceId="density-guidance" onApply={applySuggestion} onChooseFilters={focusSearch}>{!popularOnly && <button type="button" disabled={loading} onClick={() => change({ popular: null }, true)}>Show popular painters</button>}</TimelineFilterSuggestions></> :
            positioned.length ? <TimelineLanes key={`${popularOnly}-${womenOnly}`} label="Painter timeline lanes" loading={loading} height={laneCount * 54 + 12}>{positioned.map(artist => <TimelineMark key={artist.id} className="artist-mark" disabled={loading} selected={artist.slug === slug} left={artist.left} top={artist.lane * 54 + 8} width={artist.width} labelOffset={artist.labelOffset} labelWidth={artist.labelWidth} color={artist.movement.color} onSelect={() => openArtist(artist.slug)} label={`${artist.name}, ${artist.date_display}, ${artist.movement.name}, ${artist.countries.map(countryName).join(", ")}, ${artist.artwork_count} recorded works`} title={`${artist.movement.name} · ${artist.artwork_count} recorded works`} name={artist.name} date={artist.date_display} />)}</TimelineLanes> :
            <div className="state-panel"><h2>{loading ? "Opening the atlas…" : "No painters in this view"}</h2>{!loading && <><p>{activeFilters.length ? "No records match these filters in this date range." : start !== 1100 || end !== 2000 ? "No painter records overlap these years. Try a wider date range." : "Choose another date range or adjust the painter filters."}</p><div className="empty-view-actions">{activeFilters.length > 0 && <button onClick={() => { clearFilters(); searchInput.current?.focus(); }}>Remove filters</button>}{(start !== 1100 || end !== 2000) && <button onClick={() => setRange(1100, 2000)}>Show full date range</button>}</div></>}</div>}
        </TimelineGrid>
      <TimelineRangeControls start={start} end={end} minimum={1100} maximum={2000} onChange={setRange} onPreview={setRangePreview}
        scale={{ position: year => artworkYearPosition(year), yearAt: percent => artworkYearAtPosition(percent), markers: rangeMarkers }}
        endpoints={["1100", "2000"]} />
      </div>}
    </ExplorerFrame>
    {!paintings && <section className="results-section" aria-busy={loading}><div className="results-heading"><h2 id="painter-index-title">{data?.mode === "density" ? "Explore a period" : "Painter index"}</h2><p>{data?.mode === "density" ? needsFilter ? "This period is busy. Try the suggested filter, or choose your own above." : "Choose a period to explore. Busy periods may need a painter, movement or country filter." : "Choose a name for artworks, collections and sources. Work counts describe our catalogue, not a painter’s lifetime output."}</p></div>
      {error ? <p className="results-error">Results will return when the connection is restored. Use “Try again” above.</p> : data?.mode === "density" ? <ul className="density-results">{(data.periods ?? []).map(period => <li key={period.start_year}><button disabled={loading} onClick={() => selectPeriod(period.start_year, period.end_year)}>{period.start_year}–{period.end_year}<span>{period.count} {period.count === 1 ? "painter" : "painters"}{isCurrentPeriod(period, start, end) && (suggestions[0] ? ` · Try ${suggestions[0].name} · ${suggestions[0].count} painters →` : " · Choose filters →")}</span></button></li>)}</ul> :
        <div className="painter-index-scroll" role="region" aria-labelledby="painter-index-title" tabIndex={0}><ol className="artist-results">{(data?.items ?? []).map(artist => <li key={artist.id} className="bookmark-index-item"><button disabled={loading} aria-pressed={artist.slug === slug} onClick={() => openArtist(artist.slug)}><span className="movement-dot" style={{ background: artist.movement.color }} /><span><strong>{artist.name}</strong><small>{artist.date_display} · {artist.countries.map(countryName).join(", ")}</small></span><span className={`result-coverage${artist.artwork_count === 0 ? " is-missing" : ""}`}>{artist.artwork_count ? `${artist.artwork_count} ${artist.artwork_count === 1 ? "work" : "works"}` : "Works to add"}</span></button><BookmarkButton kind="artist" id={artist.id} title={artist.name} /></li>)}</ol></div>}
    </section>}
    {!paintings && slug && <RecordDrawer label="Painter details" closeLabel="Close painter details" recordKey={slug} close={closeArtist} fallbackFocusId="timeline-title"
      title={painterIndex >= 0 ? `Painter ${painterIndex + 1} of ${data?.total}` : "Painter record"}
      navigation={<nav className="painter-navigation" aria-label="Browse painters"><button type="button" aria-label="Previous painter" disabled={loading || painterIndex <= 0} onClick={() => openArtist(data!.items[painterIndex - 1].slug)}>←</button><button type="button" aria-label="Next painter" disabled={loading || painterIndex < 0 || painterIndex >= (data?.items.length ?? 0) - 1} onClick={() => openArtist(data!.items[painterIndex + 1].slug)}>→</button></nav>}>{selected.slug !== slug ? <p className="record-loading" role="status"><LoadingIndicator label="Opening painter record…" /></p> : selected.error ? <div className="record-error"><h2>Painter unavailable</h2><p>{selected.error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : selected.data && <ArtistChronologyRecord key={selected.data.id} artist={selected.data} workId={params.get("work")} onSelectWork={id => change({ work: id })} />}</RecordDrawer>}
  </>;
}
