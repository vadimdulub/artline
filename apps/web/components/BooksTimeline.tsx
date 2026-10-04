"use client";

import { useEffect, useRef, useState } from "react";
import { authorLifespanLabel, bookAxisTicks, bookTickPosition, bookYearAtPosition, bookYearLabel, positionBooks, type Book, type TimelineAuthor, type BookRange, type BooksResponse } from "@/lib/books";
import { atlasTimelineScale } from "@/lib/atlas-timeline";
import { TimelineGrid, TimelineLanes, TimelineMark } from "./TimelineGrid";
import { BooksGallery } from "./BooksGallery";
import { GalleryScrollButtons } from "./AllArtworkGallery";
import { TimelineRangeControls } from "./TimelineRangeControls";
import { TimelineZoomOut } from "./TimelineZoomOut";
import { TimelineHeader } from "./TimelineHeader";

export function BooksTimeline({ data, metadata, range, loading, error, selected, query, onBook, onAuthor, onRange, onZoomOut, onRetry, onReset, authorView = false, onAuthorView }: {
  authorView?: boolean; onAuthorView: (checked: boolean) => void;
  data?: BooksResponse; metadata?: BooksResponse; range: BookRange; loading: boolean; error?: string;
  selected: string; query: string; onBook: (book: Book, page: Book[]) => void; onAuthor: (author: TimelineAuthor) => void; onRange: (start: number, end: number) => void;
  onZoomOut: () => void; onRetry: () => void; onReset: () => void;
}) {
  const stage = useRef<HTMLDivElement>(null);
  const strip = useRef<HTMLUListElement>(null);
  const [width, setWidth] = useState(1200);
  const [rangePreview, setRangePreview] = useState<BookRange | null>(null);
  const displayRange = rangePreview ?? range;
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(entries => setWidth(entries[0].contentRect.width));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, []);
  const noun = authorView ? "authors" : "books";
  const bounds = metadata?.bounds ?? { start: -5000, end: 2000 };
  // Invalid shared URLs still reach server validation without breaking chart geometry.
  const validRange = Number.isInteger(range.start) && Number.isInteger(range.end) && range.start !== 0 && range.end !== 0 && range.start >= bounds.start && range.end <= bounds.end && range.start < range.end;
  const plotRange = validRange ? range : bounds;
  const { focused, position, ticks } = atlasTimelineScale(plotRange, bounds, width, {
    position: year => bookTickPosition(year, bounds), ticks: bookAxisTicks(bounds, width),
  });
  const gallery = data?.mode === "density";
  const books = positionBooks(gallery || authorView ? [] : data?.items ?? [], plotRange, width, 1700, position);
  const authors = positionBooks(gallery || !authorView ? [] : data?.authors ?? [], plotRange, width, 1700, position);
  const undatedBooks = gallery || authorView ? [] : (data?.items ?? []).filter(book => book.startYear === null || book.endYear === null);
  const undatedAuthors = gallery || !authorView ? [] : (data?.authors ?? []).filter(author => author.startYear === null || author.endYear === null);
  const height = Math.max(1, ...books.map(book => book.lane + 1), ...authors.map(author => author.lane + 1)) * 72 + 12;
  const rangeMarkers = metadata ? [1700, 1750, 1800, 1850, 1900, 1950, 2000]
    .filter(year => year > metadata.bounds.start && year < metadata.bounds.end)
    .filter(year => width >= 700 || year % 100 === 0)
    // Leave space for both the last marker and the right-aligned endpoint.
    .filter(year => (100 - bookTickPosition(year, metadata.bounds)) / 100 * Math.max(1, width - 24) >= 72)
    .map(year => ({ year, label: bookYearLabel(year) })) : [];

  return <div className="timeline-dark">
    <TimelineHeader controls={<><div className="books-view-switch" role="group" aria-label="Books display"><button type="button" aria-pressed={!authorView} onClick={() => onAuthorView(false)}>Books</button><button type="button" aria-pressed={authorView} onClick={() => onAuthorView(true)}>Authors</button></div>{gallery && <GalleryScrollButtons strip={strip} noun={noun} disabled={loading || !!error || !data?.total} />}</>}
      status={loading ? `Finding ${noun}…` : error ? "Connection interrupted" : `${(data?.total ?? 0).toLocaleString("en-GB")} ${noun} in this view`}
      zoom={<TimelineZoomOut disabled={!focused && validRange && !error} onClick={onZoomOut} />}>
      <h1 id="books-timeline" className="time-title book-time-title" data-bce={displayRange.start < 0 || displayRange.end < 0} tabIndex={-1} aria-label={authorView ? "Authors through time" : "Books through time"}>{Math.abs(displayRange.start)}{displayRange.start < 0 && <small>BCE</small>}<span aria-hidden="true">—</span>{Math.abs(displayRange.end)}{displayRange.end < 0 && <small>BCE</small>}</h1>
    </TimelineHeader>
    <TimelineGrid stageRef={stage} busy={loading} ticks={ticks.map(tick => ({ key: tick.year, label: tick.label, position: position(tick.year) }))}>
      {error ? <div className="state-panel" role="alert"><h2>We couldn’t load this view</h2><p>{error}</p><button onClick={onRetry}>Retry</button> <button onClick={onReset}>Reset view</button></div> :
        data?.total ? gallery ? <BooksGallery key={query} data={data} query={query} authorView={authorView} selected={selected} strip={strip} onBook={onBook} onAuthor={onAuthor} /> :
        <><TimelineLanes label={authorView ? "Authors timeline" : "Books timeline"} height={height}>
          {books.map(book => <TimelineMark key={book.id} className="book-mark" name={book.title} context={book.author} date={book.years}
            label={`${book.title}, ${book.author}, ${book.years}. Open book details`} color="#c4aa81" hasPopup="dialog"
            selected={selected === book.id} approximate={book.approximate} left={book.left} width={book.width} top={book.lane * 72 + 6} labelOffset={book.labelOffset} labelWidth={book.labelWidth} onSelect={() => onBook(book, data.items)} />)}
          {authors.map(author => <TimelineMark key={author.id} className="book-author-mark" name={author.name} context={`${author.bookCount.toLocaleString("en-GB")} ${author.bookCount === 1 ? "book" : "books"}`} date={authorLifespanLabel(author)}
            label={`${author.name}, ${authorLifespanLabel(author)}. Open author details`} color="#c4aa81" hasPopup="dialog"
            selected={selected === author.id} approximate={author.approximate} left={author.left} width={author.width} top={author.lane * 72 + 6} labelOffset={author.labelOffset} labelWidth={author.labelWidth} onSelect={() => onAuthor(author)} />)}
        </TimelineLanes>
        {(undatedBooks.length > 0 || undatedAuthors.length > 0) && <ul className="books-undated" aria-label={`${authorView ? "Authors" : "Books"} without established dates`}>
          {undatedBooks.map(book => <li key={book.id}><button type="button" aria-haspopup="dialog" onClick={() => onBook(book, data.items)}>{book.title} <small>Dates not established</small></button></li>)}
          {undatedAuthors.map(author => <li key={author.id}><button type="button" aria-haspopup="dialog" onClick={() => onAuthor(author)}>{author.name} <small>Lifespan not established</small></button></li>)}
        </ul>}</> :
        <div className="state-panel"><h2>{loading ? `Opening ${noun}…` : `No ${noun} match this view`}</h2>{!loading && <><p>Try another title, author, or idea, or clear your filters.</p><button onClick={onReset}>Clear filters</button></>}</div>}
    </TimelineGrid>
    {metadata && <TimelineRangeControls start={range.start} end={range.end} minimum={metadata.bounds.start} maximum={metadata.bounds.end}
      onChange={onRange} onPreview={setRangePreview} omitYearZero formatYear={bookYearLabel} inputPrefix={authorView ? "Author " : "Book "}
      scale={{ position: year => bookTickPosition(year, metadata.bounds), yearAt: position => bookYearAtPosition(position, metadata.bounds), markers: rangeMarkers }}
      endpoints={[bookYearLabel(metadata.bounds.start), bookYearLabel(metadata.bounds.end)]}
      disabled={Boolean(error)} />}
  </div>;
}
