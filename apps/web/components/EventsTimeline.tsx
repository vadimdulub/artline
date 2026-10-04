"use client";

import { useEffect, useRef, useState } from "react";
import { bookTickPosition, bookYearAtPosition, bookYearLabel, compressedBefore1700, positionBooks, bookAxisTicks, type BookRange } from "@/lib/books";
import { atlasTimelineScale } from "@/lib/atlas-timeline";
import type { EventsResponse, EventSuggestion } from "@/lib/events";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineZoomOut } from "./TimelineZoomOut";
import { TimelineHeader } from "./TimelineHeader";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineFilterSuggestions } from "./TimelineFilterSuggestions";

export function EventsTimeline({ data, metadata, range, loading, error, selected, onSelect, onRange, onPeriod, onZoomOut, onRetry, onReset, onSuggestion, onTop100 }: {
  data?: EventsResponse; metadata?: EventsResponse; range: BookRange; loading: boolean; error?: string;
  selected: string; onSelect: (id: string) => void; onRange: (start: number, end: number) => void; onPeriod: (start: number, end: number) => void;
  onZoomOut: () => void; onRetry: () => void; onReset: () => void; onSuggestion: (value: EventSuggestion) => void; onTop100: () => void;
}) {
  const stage = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);
  const [rangePreview, setRangePreview] = useState<BookRange | null>(null);
  const displayRange = rangePreview ?? range;
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(stage.current); return () => observer.disconnect();
  }, []);
  const filterNames = { topic: "Topic", country: "Country", region: "Region", kind: "Type" };
  const suggestions = (data?.suggested_filters ?? []).map(suggestion => ({ ...suggestion, name: `${filterNames[suggestion.key]}: ${suggestion.name}` }));
  const currentPeriod = (start: number, end: number) => start === end || start === range.start && end === range.end;
  const needsFilter = Boolean(data?.density.length && data.density.every(p => currentPeriod(p.start_year, p.end_year)));
  const focusFilters = () => document.querySelector<HTMLInputElement>('input[aria-label="Find an event"]')?.focus();
  const bounds = metadata?.bounds ?? { start: -12000, end: 2000 };
  // Keep invalid shared URLs out of chart geometry while the server reports them.
  const validRange = Number.isInteger(range.start) && Number.isInteger(range.end) && range.start !== 0 && range.end !== 0 && range.start >= bounds.start && range.end <= bounds.end && range.start < range.end;
  const plotRange = validRange ? range : bounds;
  const { focused, position, ticks } = atlasTimelineScale(plotRange, bounds, width, {
    position: year => bookTickPosition(year, bounds), ticks: bookAxisTicks(bounds, width),
  });
  const positioned = positionBooks(data?.items ?? [], plotRange, width, 1700, position);
  const height = Math.max(4, ...positioned.map(event => event.lane + 1)) * 64 + 12;
  const earlyCompressed = !focused && compressedBefore1700(bounds);
  const markers = [1700, 1750, 1800, 1850, 1900, 1950].filter(year => width >= 700 || year % 100 === 0).map(year => ({ year, label: String(year) }));

  return <div className={`timeline-dark${earlyCompressed ? " books-compressed-scale" : ""}`}>
    <TimelineHeader controls={<div className="timeline-secondary-tools"><a className="timeline-index-link" href="#event-index">Event index</a></div>}
      status={loading ? "Finding events…" : error ? "Connection interrupted" : `${(data?.total ?? 0).toLocaleString("en-GB")} events in this view`}
      zoom={<TimelineZoomOut disabled={!focused && validRange && !error} onClick={onZoomOut} />}>
      <h1 id="events-timeline" className="time-title book-time-title" data-bce={displayRange.start < 0 || displayRange.end < 0} tabIndex={-1} aria-label="Events through time">{Math.abs(displayRange.start)}{displayRange.start < 0 && <small>BCE</small>}<span aria-hidden="true">—</span>{Math.abs(displayRange.end)}{displayRange.end < 0 && <small>BCE</small>}</h1>
    </TimelineHeader>
    <TimelineGrid stageRef={stage} busy={loading} ticks={ticks.map(t => ({ key: t.year, label: t.label, position: position(t.year) }))}>
      {earlyCompressed && <div className="book-scale-break" style={{ left: `${bookTickPosition(1700, bounds)}%` }} aria-hidden="true" />}
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={onRetry}>Retry</button> <button onClick={onReset}>Reset view</button></div> :
        data?.mode === "density" ? <><TimelineOverview key={`${range.start}-${range.end}`} suggestion={suggestions[0]} periods={data.density} start={range.start} end={range.end} disabled={loading} noun="events" guidanceId={null}
          formatPeriod={(start, end) => start < 0 && end === -1 && range.end > 0 ? "BCE" : `${bookYearLabel(start)}–${bookYearLabel(end)}`}
          position={position} footnote={null}
          onSelect={(start, end) => { if (currentPeriod(start, end)) { if (suggestions[0]) onSuggestion(suggestions[0]); else focusFilters(); } else onPeriod(start, end); }} />
          <TimelineFilterSuggestions suggestions={suggestions} noun="events" needsFilter={needsFilter} disabled={loading} guidanceId="events-density-guidance" showGuidance={false} onApply={onSuggestion} onChooseFilters={focusFilters}>
            <button type="button" disabled={loading} onClick={onTop100}>Show Top 100 events</button>
          </TimelineFilterSuggestions></> :
        positioned.length ? <TimelineLanes label="Events timeline" height={height}>
          {positioned.map(event => <TimelineMark key={event.id} className="book-author-mark" name={event.title} date={event.years}
            label={`${event.title}, ${event.years}. Open event details`} color={event.kind === "Period" ? "#76b8b5" : event.kind === "Movement" ? "#b4bb80" : "#ad8d5e"} hasPopup="dialog"
            selected={selected === event.id} approximate={event.approximate} left={event.left} width={event.width} top={event.lane * 64 + 8} labelOffset={event.labelOffset} labelWidth={event.labelWidth} onSelect={() => onSelect(event.id)} />)}
        </TimelineLanes> : <div className="state-panel"><h2>{loading ? "Opening the events timeline…" : data?.total ? "Dates are not established for these events" : "No events match this view"}</h2>{!loading && <><p>{data?.total ? "Read these records in the index below." : "Try another event, topic, or place, or reset your filters."}</p><button onClick={onReset}>Reset view</button></>}</div>}
    </TimelineGrid>
    <TimelineRangeControls start={range.start} end={range.end} minimum={bounds.start} maximum={bounds.end} onChange={onRange} onPreview={setRangePreview} omitYearZero formatYear={bookYearLabel} inputPrefix="Event "
      scale={{ position: year => bookTickPosition(year, bounds), yearAt: position => bookYearAtPosition(position, bounds), markers }} endpoints={[bookYearLabel(bounds.start), bookYearLabel(bounds.end)]} disabled={Boolean(error)} />
  </div>;
}
