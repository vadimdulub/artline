"use client";
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
import { TimelineZoomOut } from "./TimelineZoomOut";
import { TimelineHeader } from "./TimelineHeader";
import "./AllAtlas.css";
import "./PainterPaintings.css";

export function PainterPaintings({ filters, start, end, setRange, onPeriod, viewSwitch }: { filters: string; start: number; end: number; setRange: (start: number, end: number) => void; onPeriod: (start: number, end: number) => void; viewSwitch: ReactNode }) {
  const params = new URLSearchParams(useQueryString());
  const selected = params.get("painting") ?? "";
  const request = new URLSearchParams({ selection: "true", type: "artwork", start: String(start), end: String(end), highlights: "false", artwork_image_only: "true" });
  for (const [key, value] of new URLSearchParams(filters)) if (!["start", "end", "fit"].includes(key)) request.append(`artwork_${key}`, value);
  const scope = timelineRequestKey(request);
  if (params.get("painting_after")) request.set("after_artwork", params.get("painting_after")!);
  const key = timelineRequestKey(request);
  const [retry, setRetry] = useState(0);
  const [result, setResult] = useState<{ key: string; attempt: number; data?: AtlasResponse; error?: string }>();
  const [preview, setPreview] = useState<{ start: number; end: number } | null>(null);
  const [width, setWidth] = useState(1000);
  const stage = useRef<HTMLDivElement>(null);
  const busy = result?.key !== key || result?.attempt !== retry;
  const data = !busy ? result?.data : undefined;
  const error = !busy ? result?.error : undefined;
  useFitYears(params.get("fit") === "true", !!data && !busy && !error, data?.matchedRange);
  const lane = data?.lanes[0];
  const years = preview ?? { start, end };
  const { focused, position, ticks } = atlasTimelineScale({ start, end }, { start: 1100, end: 2000 }, width, {
    position: artworkYearPosition, ticks: visibleArtworkTicks(1100, 2000, width).map(year => ({ year, label: String(year) })),
  });
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => apiRequest<AtlasResponse>(`atlas?${key}`, { signal: controller.signal })
      .then(data => { if (!controller.signal.aborted) setResult({ key, attempt: retry, data }); })
      .catch(error => { if (!controller.signal.aborted) setResult({ key, attempt: retry, error: errorMessage(error) }); }), 140);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [key, retry]);
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, []);
  function open(item: AtlasItem) { updateQuery({ painting: item.id }, true); }
  function close() { updateQuery({ painting: null }, true); }
  function changeRange(a: number, b: number) { setPreview(null); setRange(a, b); }
  const navigation = useRecordNavigation(selected ? `atlas?${scope}` : null, selected, id => updateQuery({ painting: id }, true));
  return <div className="timeline-dark painter-paintings">
    <TimelineHeader controls={viewSwitch}
      status={busy ? "Finding paintings…" : error ? "Couldn’t load" : `${lane?.total.toLocaleString("en-GB") ?? 0} artworks`}
      zoom={<TimelineZoomOut disabled={!focused} onClick={() => changeRange(1100, 2000)} />}>
      <h1 id="timeline-title" className="time-title" tabIndex={-1}><span className="sr-only">Artwork creation dates: </span>{years.start}<span aria-hidden="true">—</span><span className="sr-only"> to </span>{years.end}</h1>
    </TimelineHeader>
    <TimelineGrid stageRef={stage} busy={busy} ticks={ticks.map(tick => ({ key: tick.year, label: tick.label, position: position(tick.year) }))}>
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load these paintings</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : busy ? <div className="state-panel"><LoadingIndicator label="Finding paintings…" /></div> : lane?.items.length ? <>
        <AllArtworkGallery key={key} lane={lane} query={key} busy={busy} selected={selected} select={open} />
        {lane.mode === "density" && <details className="all-artwork-density"><summary>Explore artworks by year</summary><TimelineOverview disabled={busy} periods={lane.density} start={start} end={end} position={position} showCurrentAction={false} noun="artworks" footnote="" onSelect={(a, b) => onPeriod(a, Math.max(a + 1, b))} /></details>}
      </> : <div className="state-panel"><h2>No paintings in this view</h2><p>{start > 1970 ? "Artwork coverage ends at 1970. Choose earlier years." : "Try another painter or a wider date range."}</p></div>}
    </TimelineGrid>
    <TimelineRangeControls start={start} end={end} minimum={1100} maximum={2000} onChange={changeRange} onPreview={setPreview} endpoints={["1100", "2000"]} scale={{ position: artworkYearPosition, yearAt: artworkYearAtPosition, markers: [1400, 1600, 1800].map(year => ({ year, label: String(year) })) }} />
    {selected && <AllArtworkDrawer id={selected} close={close} navigation={navigation} fallbackFocusId="timeline-title" />}
  </div>;
}
