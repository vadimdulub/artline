"use client";

import { useRef, useState, type CSSProperties } from "react";
import type { TimelineResponse } from "@/lib/types";

// Colour identifies a part of the timeline, independently of movement metadata.
function periodColor(year: number) {
  if (year < 1400) return "#789dc8";
  if (year < 1600) return "#76b8b5";
  if (year < 1750) return "#b4bb80";
  if (year < 1850) return "#dcac70";
  return "#db8a78";
}

export function TimelineOverview({ periods, start, end, disabled, onSelect }: {
  periods: TimelineResponse["periods"]; start: number; end: number; disabled: boolean;
  onSelect: (start: number, end: number) => void;
}) {
  const [active, setActive] = useState<number | null>(null);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  const maximum = Math.max(1, ...periods.map(period => period.count));
  const span = Math.max(1, end - start + 1);
  const selected = active === null ? null : periods[active];

  return <div className="timeline-overview">
    <div className="overview-caption"><h2>Painters through time</h2><p aria-live="polite">{selected ? <><strong>{selected.count.toLocaleString("en-GB")} painters</strong> · {selected.start_year}–{selected.end_year}</> : "Choose a period to explore its painters"}</p></div>
    <div className="period-chart" role="group" aria-label="Explore painters by period">
      <div className="period-grid" aria-hidden="true">{[.25, .5, .75, 1].map(fraction => <span key={fraction} style={{ bottom: `${fraction * 82}%` }}><i>{Math.round(maximum * fraction).toLocaleString("en-GB")}</i></span>)}</div>
      {periods.map((period, index) => <button key={period.start_year} ref={node => { buttons.current[index] = node; }}
        type="button" className="period-column" disabled={disabled || (period.start_year === start && period.end_year === end)}
        aria-label={`Explore ${period.start_year}–${period.end_year}, ${period.count.toLocaleString("en-GB")} painters`}
        style={{ "--column-left": `${(period.start_year - start) / span * 100}%`, "--column-width": `${(period.end_year - period.start_year + 1) / span * 100}%`, "--period-color": periodColor(period.start_year), "--bar-height": `${period.count / maximum * 82}%`, "--bar-width": `${period.count / maximum * 100}%` } as CSSProperties}
        onPointerEnter={() => setActive(index)} onFocus={() => setActive(index)}
        onClick={() => onSelect(period.start_year, Math.max(period.start_year + 1, period.end_year))}
        onKeyDown={event => {
          const next = event.key === "ArrowRight" ? index + 1 : event.key === "ArrowLeft" ? index - 1 : event.key === "Home" ? 0 : event.key === "End" ? periods.length - 1 : null;
          if (next !== null) { event.preventDefault(); buttons.current[Math.max(0, Math.min(periods.length - 1, next))]?.focus(); }
        }}>
        <span className="period-label" aria-hidden="true">{period.start_year}–{period.end_year}</span>
        <span className="period-count" aria-hidden="true">{period.count.toLocaleString("en-GB")}</span>
        <span className="period-track" aria-hidden="true"><span className="period-bar" /></span>
      </button>)}
    </div>
    <p className="overview-footnote">Bars show painter counts; colours identify periods.</p>
  </div>;
}
