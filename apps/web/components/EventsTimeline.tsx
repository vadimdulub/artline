"use client";

import { LoadingIndicator } from "./LoadingIndicator";
import { useEffect, useRef, useState } from "react";
import { bookTickPosition, bookYearAtPosition, bookYearLabel, compressedBefore1700, positionBooks, bookAxisTicks, type BookRange } from "@/lib/books";
import type { EventsResponse, EventSuggestion } from "@/lib/events";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineFilterSuggestions } from "./TimelineFilterSuggestions";

export function EventsTimeline({ data, metadata, range, loading, error, selected, onSelect, onRange, onRetry, onReset, onSuggestion, onTop100 }: {
  data?: EventsResponse; metadata?: EventsResponse; range: BookRange; loading: boolean; error?: string;
  selected: string; onSelect: (id: string) => void; onRange: (start: number, end: number) => void;
  onRetry: () => void; onReset: () => void; onSuggestion: (value: EventSuggestion) => void; onTop100: () => void;
}) {
  const stage = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);
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
  const positioned = positionBooks(data?.items ?? [], bounds, Math.max(1, width - 16));
  const height = Math.max(4, ...positioned.map(event => event.lane + 1)) * 64 + 12;
  const ticks = bookAxisTicks(bounds, width);
  const earlyCompressed = compressedBefore1700(bounds);
  const markers = [1700, 1750, 1800, 1850, 1900, 1950].filter(year => width >= 700 || year % 100 === 0).map(year => ({ year, label: String(year) }));

  return <div className={`timeline-dark${earlyCompressed ? " books-compressed-scale" : ""}`}>
    <div className="timeline-heading-row">
      <div><p className="range-caption">Events · selected years</p><h1 id="events-timeline" className="time-title book-time-title" tabIndex={-1} aria-label="Events through time">{Math.abs(range.start)}{range.start < 0 && <small>BCE</small>}<span aria-hidden="true">—</span>{Math.abs(range.end)}{range.end < 0 && <small>BCE</small>}</h1></div>
      <div className="timeline-counter" role="status">{loading ? <LoadingIndicator label="Finding events…" /> : error ? "Connection interrupted" : `${(data?.total ?? 0).toLocaleString("en-GB")} events in this view`}<small><a href="#event-index">Event index ↓</a></small></div>
    </div>
    <TimelineGrid stageRef={stage} busy={loading} selection={{ left: bookTickPosition(range.start, bounds), right: bookTickPosition(range.end, bounds) }} ticks={ticks.map(t => ({ key: t.year, label: t.label, position: bookTickPosition(t.year, bounds) }))}>
      {earlyCompressed && <div className="book-scale-break" style={{ left: `${bookTickPosition(1700, bounds)}%` }} aria-hidden="true" />}
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={onRetry}>Retry</button> <button onClick={onReset}>Reset view</button></div> :
        data?.mode === "density" ? <><TimelineOverview key={`${range.start}-${range.end}`} suggestion={suggestions[0]} periods={data.density} start={range.start} end={range.end} disabled={loading} noun="events" guidanceId="events-density-guidance"
          formatPeriod={(start, end) => start < 0 && end === -1 && range.end > 0 ? "BCE" : `${bookYearLabel(start)}–${bookYearLabel(end)}`}
          position={year => bookTickPosition(year, bounds)} footnote="An event or historical period is counted in each interval its recorded dates overlap."
          onSelect={(start, end) => { if (currentPeriod(start, end)) { if (suggestions[0]) onSuggestion(suggestions[0]); else focusFilters(); } else onRange(start, end); }} />
          <TimelineFilterSuggestions suggestions={suggestions} noun="events" needsFilter={needsFilter} disabled={loading} guidanceId="events-density-guidance" onApply={onSuggestion} onChooseFilters={focusFilters}>
            <button type="button" disabled={loading} onClick={onTop100}>Show Top 100 events</button>
          </TimelineFilterSuggestions></> :
        positioned.length ? <TimelineLanes label="Events timeline" descriptionId="events-timeline-help" height={height}>
          {positioned.map(event => <TimelineMark key={event.id} className="book-author-mark" name={event.title} date={event.years}
            label={`${event.title}, ${event.years}. Open event details`} color={event.kind === "Period" ? "#76b8b5" : event.kind === "Movement" ? "#b4bb80" : "#ad8d5e"} hasPopup="dialog"
            selected={selected === event.id} approximate={event.approximate} left={event.left} width={event.width} top={event.lane * 64 + 8} labelOffset={event.labelOffset} labelWidth={event.labelWidth} onSelect={() => onSelect(event.id)} />)}
        </TimelineLanes> : <div className="state-panel"><h2>{loading ? "Opening the events timeline…" : data?.total ? "Dates are not established for these events" : "No events match this view"}</h2>{!loading && <><p>{data?.total ? "Read these records in the index below." : "Try another event, topic, or place, or reset your filters."}</p><button onClick={onReset}>Reset view</button></>}</div>}
    </TimelineGrid>
    <p className="timeline-scroll-help" id="events-timeline-help">{data?.mode === "density" ? "Choose a period or narrow the filters to see individual events." : "Select an event to read its story. Lines show recorded spans; dashed lines show uncertainty."}{Boolean(data?.undatedTotal) && ` ${data!.undatedTotal} ${data!.undatedTotal === 1 ? "record has" : "records have"} no established date; see the full-range index.`}</p>
    <TimelineRangeControls start={range.start} end={range.end} minimum={bounds.start} maximum={bounds.end} onChange={onRange} omitYearZero formatYear={bookYearLabel} inputPrefix="Event "
      scale={{ position: year => bookTickPosition(year, bounds), yearAt: position => bookYearAtPosition(position, bounds), markers }} endpoints={[bookYearLabel(bounds.start), bookYearLabel(bounds.end)]} disabled={Boolean(error)} />
  </div>;
}
