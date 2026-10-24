"use client";
import type { MapItem } from "@/lib/map";
import { CatalogueMap } from "./CatalogueMap";
import { useFitYears } from "./use-fit-years";
import { timelineRequestKey } from "@/lib/timeline-request";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiRequest, errorMessage } from "@/lib/api";
import type { AtlasItem, AtlasResponse } from "@/lib/atlas";
import { artworkYearAtPosition, artworkYearPosition, visibleArtworkTicks } from "@/lib/timeline";
import { atlasTimelineScale } from "@/lib/atlas-timeline";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { AllArtworkGallery } from "./AllArtworkGallery";
import { AllArtworkDrawer } from "./AllArtworkDrawer";
import { LoadingIndicator } from "./LoadingIndicator";
import { useRecordNavigation } from "./RecordNavigation";
import { TimelineGrid } from "./TimelineGrid";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineHeader } from "./TimelineHeader";
import "./AllAtlas.css";
import "./PainterPaintings.css";

export function PainterPaintings({ filters, start, end, setRange, onPeriod, viewSwitch, mapView = false, artists }: { artists?: { items: MapItem[]; total: number; loading: boolean; error?: string; retry: () => void; open: (item: MapItem) => void }; mapView?: boolean; filters: string; start: number; end: number; setRange: (start: number, end: number) => void; onPeriod: (start: number, end: number) => void; viewSwitch: ReactNode }) {
  const params = new URLSearchParams(useQueryString());
  const selected = params.get("painting") ?? "";
  const showPaintings = true;
  const showArtists = mapView;
  const combinedMap = new URLSearchParams({ canvas: "map", selection: "true", start: String(start), end: String(end), highlights: "false" });
  ["artwork", "book", "event"].forEach(kind => combinedMap.append("type", kind));
  for (const [key, value] of new URLSearchParams(filters)) if (!["start", "end", "fit"].includes(key)) combinedMap.append(`artwork_${key}`, value);
  const request = new URLSearchParams({ selection: "true", type: "artwork", start: String(start), end: String(end), highlights: "false", artwork_image_only: String(!mapView) });
  for (const [key, value] of new URLSearchParams(filters)) if (!["start", "end", "fit"].includes(key)) request.append(`artwork_${key}`, value);
  const scope = timelineRequestKey(request);
  if (params.get("painting_after")) request.set("after_artwork", params.get("painting_after")!);
  const key = timelineRequestKey(request);
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; attempt: number; data?: AtlasResponse; error?: string }>();
  const [preview, setPreview] = useState<{ start: number; end: number } | null>(null);
  const [width, setWidth] = useState(1000);
  const stage = useRef<HTMLDivElement>(null);
  const busy = showPaintings && (result?.key !== key || result?.attempt !== retry);
  const data = showPaintings && !busy ? result?.data : undefined;
  const error = showPaintings && !busy ? result?.error : undefined;
  useFitYears(!mapView && params.get("fit") === "true", !!data && !busy && !error, data?.matchedRange);
  const lane = data?.lanes[0];
  const years = preview ?? { start, end };
  const { position, ticks } = atlasTimelineScale({ start, end }, { start: 1100, end: 2000 }, width, {
    position: artworkYearPosition, ticks: visibleArtworkTicks(1100, 2000, width).map(year => ({ year, label: String(year) })),
  });
  useEffect(() => {
    if (!showPaintings) return;
    const controller = new AbortController();
    const timer = setTimeout(() => apiRequest<AtlasResponse>(`atlas?${key}`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setResult({ key, attempt: retry, data }); })
      .catch(error => { if (!controller.signal.aborted) setResult({ key, attempt: retry, error: errorMessage(error) }); }), 140);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [key, retry, showPaintings]);
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, [mapView]);
  function open(item: AtlasItem) { updateQuery({ painting: item.id }, true); }
  function close() { updateQuery({ painting: null }, true); }
  function changeRange(a: number, b: number) { setPreview(null); setRange(a, b); }
  const navigation = useRecordNavigation(selected ? `atlas?${scope}` : null, selected, id => updateQuery({ painting: id }, true));
  return <div className="timeline-dark painter-paintings">
    {!mapView && <TimelineHeader controls={viewSwitch}
      status={busy ? "Finding paintings…" : error ? "Couldn’t load" : `${lane?.total.toLocaleString("en-GB") ?? 0} artworks`}>
      <h1 id="timeline-title" className="time-title" tabIndex={-1}><span className="sr-only">Artwork creation dates: </span>{years.start}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{years.end}</h1>
    </TimelineHeader>}
    {mapView ? <CatalogueMap headingId="timeline-title" items={[
      ...(showArtists ? artists?.items ?? [] : []),
      ...(lane?.items ?? []).map(item => ({ id: item.id, kind: "artwork" as const, title: item.title, context: item.context, years: item.years, image: item.media_url })),
    ]} total={(showArtists ? artists?.total ?? 0 : 0) + (lane?.total ?? 0)} loading={busy || (showArtists && !!artists?.loading)} error={error ?? (showArtists ? artists?.error : undefined)} onRetry={() => { setRetry(v => v + 1); artists?.retry(); }} range={{ start, end }} layerPicker={<a className="map-add-layers" href={`/all?${combinedMap}`}>Add books or events</a>}
      onOpen={item => item.kind === "artist" ? artists?.open(item) : updateQuery({ painting: item.id, artist: null }, true)}>
    </CatalogueMap> : <TimelineGrid stageRef={stage} busy={busy} ticks={ticks.map(tick => ({ key: tick.year, label: tick.label, position: position(tick.year) }))}>
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load these paintings</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : busy ? <div className="state-panel"><LoadingIndicator label="Finding paintings…" /></div> : lane?.items.length ? <>
        <AllArtworkGallery key={key} lane={lane} query={key} busy={busy} selected={selected} select={open} />
        {lane.mode === "density" && <details className="all-artwork-density"><summary>Explore artworks by year</summary><TimelineOverview disabled={busy} periods={lane.density} start={start} end={end} position={position} showCurrentAction={false} noun="artworks" footnote="" onSelect={(a, b) => onPeriod(a, Math.max(a + 1, b))} /></details>}
      </> : <div className="state-panel"><h2>No paintings in this view</h2><p>{start > 1970 ? "Artwork coverage ends at 1970. Choose earlier years." : "Try another painter or a wider date range."}</p></div>}
    </TimelineGrid>}
    {!mapView && <TimelineRangeControls start={start} end={end} minimum={1100} maximum={2000} onChange={changeRange} onPreview={setPreview} endpoints={["1100", "2000"]} scale={{ position: artworkYearPosition, yearAt: artworkYearAtPosition, markers: [1400, 1600, 1800].map(year => ({ year, label: String(year) })) }} />}
    {selected && <AllArtworkDrawer id={selected} close={close} navigation={navigation} fallbackFocusId="timeline-title" />}
  </div>;
}
