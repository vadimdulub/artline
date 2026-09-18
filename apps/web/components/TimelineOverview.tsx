"use client";

import { useRef, useState, type CSSProperties } from "react";
import type { TimelineResponse } from "@/lib/types";
import { isCurrentPeriod } from "@/lib/timeline";

// Colour identifies a part of the timeline, independently of movement metadata.
function periodColor(year: number) {
  if (year < 1400) return "#789dc8";
  if (year < 1600) return "#76b8b5";
  if (year < 1750) return "#b4bb80";
  if (year < 1850) return "#dcac70";
  return "#db8a78";
}

export function TimelineOverview({ periods, start, end, disabled, suggestion, onSelect, noun = "painters", formatPeriod, position, footnote, color, currentAction, guidanceId = "density-guidance" }: {
  periods: TimelineResponse["periods"]; start: number; end: number; disabled: boolean;
  suggestion?: { name: string; count: number };
  onSelect: (start: number, end: number) => void;
  noun?: "painters" | "books" | "authors" | "events" | "artworks";
  formatPeriod?: (start: number, end: number) => string;
  position?: (year: number) => number;
  footnote?: string;
  guidanceId?: string;
  color?: string;
  currentAction?: string;
}) {
  const [active, setActive] = useState<number | null>(null);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const maximum = Math.max(1, ...periods.map(period => period.count));
  const span = Math.max(1, end - start + 1);
  const selected = periods.find(period => period.start_year === active);
  const label = (from: number, to: number) => formatPeriod ? formatPeriod(from, to) : `${from}–${to}`;
  const current = (period: typeof periods[number]) => noun === "painters" ? isCurrentPeriod(period, start, end) : period.start_year === period.end_year || period.start_year === start && period.end_year === end;

  return <div className="timeline-overview">
    <div className="overview-caption"><h2>{noun[0].toUpperCase() + noun.slice(1)} through time</h2><p aria-live="polite">{selected ? <><strong>{selected.count.toLocaleString("en-GB")} {noun}</strong> · {label(selected.start_year, selected.end_year)}</> : `Choose a period to explore its ${noun}`}</p></div>
    <div className={`period-chart${periods.length > 26 ? " compact-counts" : ""}`} role="group" aria-label={`Explore ${noun} by period`}>
      <div className="period-grid" aria-hidden="true">{[.25, .5, .75, 1].map(fraction => <span key={fraction} style={{ bottom: `${fraction * 82}%` }}><i>{Math.round(maximum * fraction).toLocaleString("en-GB")}</i></span>)}</div>
      {periods.map((period, index) => <button key={period.start_year} ref={node => { buttons.current[index] = node; }}
        type="button" className="period-column" disabled={disabled}
        aria-label={current(period) ? suggestion ? `Filter by ${suggestion.name}, ${suggestion.count} ${noun}` : `${currentAction ?? "Choose filters for"} ${label(period.start_year, period.end_year)}, ${period.count} ${noun}` : `Explore ${label(period.start_year, period.end_year)}, ${period.count.toLocaleString("en-GB")} ${noun}`}
        aria-describedby={guidanceId}
        title={current(period) ? suggestion ? `Apply the ${suggestion.name} filter and keep these years` : currentAction ?? "Choose another filter to narrow these years" : undefined}
        style={{ "--column-left": `${position ? position(period.start_year) : (period.start_year - start) / span * 100}%`, "--column-width": `${position ? Math.min(100, position(period.end_year === -1 ? 1 : period.end_year + 1)) - position(period.start_year) : (period.end_year - period.start_year + 1) / span * 100}%`, "--period-color": color ?? periodColor(period.start_year), "--bar-height": `${period.count / maximum * 82}%`, "--bar-width": `${period.count / maximum * 100}%`, "--bar-minimum": period.count ? "4px" : "0px" } as CSSProperties}
        onPointerEnter={() => setActive(period.start_year)} onFocus={() => setActive(period.start_year)}
        onClick={() => onSelect(period.start_year, period.end_year)}
        onKeyDown={event => {
          const next = event.key === "ArrowRight" ? index + 1 : event.key === "ArrowLeft" ? index - 1 : event.key === "Home" ? 0 : event.key === "End" ? periods.length - 1 : null;
          if (next !== null) { event.preventDefault(); buttons.current[Math.max(0, Math.min(periods.length - 1, next))]?.focus(); }
        }}>
        <span className="period-label" aria-hidden="true">{label(period.start_year, period.end_year)}</span>
        <span className="period-count" aria-hidden="true">{period.count.toLocaleString("en-GB")}</span>
        <span className="period-track" aria-hidden="true"><span className="period-bar" /></span>
        {current(period) && <span className="period-action" aria-hidden="true">{suggestion ? `Try ${suggestion.name} · ${suggestion.count} ${noun} →` : `${currentAction ?? "Choose filters"} →`}</span>}
      </button>)}
    </div>
    <p className="overview-footnote">{footnote ?? "Counts include painters whose life or activity overlaps each period. A painter can appear in more than one period."}</p>
  </div>;
}
