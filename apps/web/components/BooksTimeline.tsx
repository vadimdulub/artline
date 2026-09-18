"use client";

import { LoadingIndicator } from "./LoadingIndicator";
import { useEffect, useRef, useState } from "react";
import { authorLifespanLabel, bookTickPosition, bookYearAtPosition, bookYearLabel, compressedBefore1700, positionBooks, bookAxisTicks, type BookSuggestion, type BookRange, type BooksResponse } from "@/lib/books";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { AtlasCheckbox } from "./AtlasFilters";
import { TimelineOverview } from "./TimelineOverview";
import { TimelineFilterSuggestions } from "./TimelineFilterSuggestions";

export function BooksTimeline({ data, metadata, range, loading, error, selected, onSelect, onRange, onRetry, onReset, onSuggestion, onTop100, authorView = false, onAuthorView }: {
  authorView?: boolean; onAuthorView: (checked: boolean) => void;
  data?: BooksResponse; metadata?: BooksResponse; range: BookRange; loading: boolean; error?: string;
  selected: string; onSelect: (id: string) => void; onRange: (start: number, end: number) => void;
  onRetry: () => void; onReset: () => void; onSuggestion: (suggestion: BookSuggestion) => void; onTop100: () => void;
}) {
  const stage = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1200);
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, []);
  const filterNames = { language: "Language", country: "Country", region: "Region", author: "Author" };
  const suggestions = (data?.suggested_filters ?? []).map(suggestion => ({ ...suggestion, name: `${filterNames[suggestion.key]}: ${suggestion.name}` }));
  const currentPeriod = (start: number, end: number) => start === end || start === range.start && end === range.end;
  const needsFilter = Boolean(data?.density.length && data.density.every(period => currentPeriod(period.start_year, period.end_year)));
  const focusFilters = () => document.querySelector<HTMLInputElement>('input[aria-label="Find a book or author"]')?.focus();
  function selectPeriod(start: number, end: number) {
    if (currentPeriod(start, end)) {
      if (suggestions[0]) onSuggestion(suggestions[0]); else focusFilters();
    } else onRange(start, end);
  }
  const noun = authorView ? "authors" : "books";
  const timelineItems = authorView ? (data?.authors ?? []).map(author => ({ ...author, title: author.name, author: undefined, years: authorLifespanLabel(author) })) : data?.items ?? [];
  const bounds = metadata?.bounds ?? { start: -5000, end: 2000 };
  const positioned = positionBooks<(typeof timelineItems)[number]>(timelineItems, bounds, Math.max(1, width - 16));
  const height = Math.max(4, ...positioned.map(book => book.lane + 1)) * 72 + 12;
  const ticks = bookAxisTicks(bounds, width);
  const earlyCompressed = compressedBefore1700(bounds);
  const rangeMarkers = metadata ? [1700, 1750, 1800, 1850, 1900, 1950, 2000]
    .filter(year => year > metadata.bounds.start && year < metadata.bounds.end)
    .filter(year => width >= 700 || year % 100 === 0)
    // Leave space for both the last marker and the right-aligned endpoint.
    .filter(year => (100 - bookTickPosition(year, metadata.bounds)) / 100 * Math.max(1, width - 24) >= 72)
    .map(year => ({ year, label: bookYearLabel(year) })) : [];

  return <div className={`timeline-dark${earlyCompressed ? " books-compressed-scale" : ""}`}>
    <div className="timeline-heading-row">
      <div><p className="range-caption">{authorView ? "Authors · life periods" : "Books · selected years"}</p><h1 id="books-timeline" className="time-title book-time-title" tabIndex={-1} aria-label={authorView ? "Authors through time" : "Books through time"}>{Math.abs(range.start)}{range.start < 0 && <small>BCE</small>}<span aria-hidden="true">—</span>{Math.abs(range.end)}{range.end < 0 && <small>BCE</small>}</h1></div>
      <div className="books-view-controls">
        <AtlasCheckbox label="Show author lifespans" checked={authorView} onChange={onAuthorView} />
        <div className="timeline-counter" role="status">{loading ? <LoadingIndicator label={`Finding ${noun}…`} /> : error ? "Connection interrupted" : `${(data?.total ?? 0).toLocaleString("en-GB")} ${noun} in this view`}<small><a href="#shelf-title">{authorView ? "Author index" : "Book index"} ↓</a></small></div>
      </div>
    </div>
    <TimelineGrid stageRef={stage} busy={loading} selection={{ left: bookTickPosition(range.start, bounds), right: bookTickPosition(range.end, bounds) }} ticks={ticks.map(tick => ({ key: tick.year, label: tick.label, position: bookTickPosition(tick.year, bounds) }))}>
      {earlyCompressed && <div className="book-scale-break" style={{ left: `${bookTickPosition(1700, bounds)}%` }} aria-hidden="true" />}
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={onRetry}>Retry</button> <button onClick={onReset}>Reset view</button></div> :
        data?.mode === "density" ? <><TimelineOverview key={`${range.start}-${range.end}`} suggestion={suggestions[0]} periods={data.density} start={range.start} end={range.end} disabled={loading} noun={noun} guidanceId="books-density-guidance"
          formatPeriod={(start, end) => start < 0 && end === -1 && range.end > 0 ? "BCE" : `${bookYearLabel(start)}–${bookYearLabel(end)}`}
          position={year => bookTickPosition(year, bounds)}
          footnote={authorView ? "Each author is counted once per period. Life dates may overlap several periods." : "A book can appear in each period its recorded dates overlap."}
          onSelect={selectPeriod} />
          <TimelineFilterSuggestions suggestions={suggestions} noun={noun} needsFilter={needsFilter} disabled={loading} guidanceId="books-density-guidance" onApply={onSuggestion} onChooseFilters={focusFilters}>
            <button type="button" disabled={loading} onClick={onTop100}>Show Top 100 books</button>
          </TimelineFilterSuggestions></> :
        positioned.length ? <TimelineLanes label={authorView ? "Authors timeline" : "Books timeline"} descriptionId="books-timeline-help" height={height}>
          {positioned.map(book => <TimelineMark key={book.id} className={authorView ? "book-author-mark" : "book-mark"} name={book.title} context={book.author} date={book.years}
            label={`${book.title}${book.author ? `, ${book.author}` : ""}, ${book.years}. Open ${authorView ? "author" : "book"} details`} color="#ad8d5e" hasPopup="dialog"
            selected={selected === book.id} approximate={book.approximate}
            left={book.left} width={book.width} top={book.lane * 72 + 8} labelOffset={book.labelOffset} labelWidth={book.labelWidth}
            onSelect={() => onSelect(book.id)} />)}
        </TimelineLanes> :
        <div className="state-panel"><h2>{loading ? `Opening the ${noun} timeline…` : data?.total ? `Dates are not established for these ${noun}` : `No ${noun} match this view`}</h2>{!loading && <>{data?.total ? <p>Choose an entry in the index below to read its details. These records will appear on the timeline when their dates are established.</p> : <><p>Try another title, author, or idea, or clear your filters.</p><button onClick={onReset}>Clear filters</button></>}</>}</div>}
    </TimelineGrid>
    <p className="timeline-scroll-help" id="books-timeline-help">{authorView ? "Years filter authors’ recorded life dates. Dashed lines show uncertainty; a single recorded date appears as a marker." : data?.mode === "density" ? "Choose a period or narrow the filters to see individual books." : "Select a title to read about the book. Dashed lines show approximate dates."}{Boolean(data?.undatedTotal) && (authorView ? ` ${data!.undatedTotal.toLocaleString("en-GB")} authors have no plottable lifespan; find them in the full-range author index.` : ` ${data!.undatedTotal.toLocaleString("en-GB")} books have no established date; find them in the full-range book index.`)}</p>
    {metadata && <TimelineRangeControls start={range.start} end={range.end} minimum={metadata.bounds.start} maximum={metadata.bounds.end}
      onChange={onRange} omitYearZero formatYear={bookYearLabel} inputPrefix={authorView ? "Author " : "Book "}
      scale={{ position: year => bookTickPosition(year, metadata.bounds), yearAt: position => bookYearAtPosition(position, metadata.bounds), markers: rangeMarkers }}
      endpoints={[bookYearLabel(metadata.bounds.start), bookYearLabel(metadata.bounds.end)]}
      disabled={Boolean(error)} />}
  </div>;
}
