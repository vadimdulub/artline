"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import { artworkDate, artworkMedium, displayMetadata } from "@/lib/display-metadata";
import type { ArtistDetail, Artwork } from "@/lib/types";
import { ArtworkImage } from "./ArtworkViewer";
import styles from "./ArtistArtworkTimeline.module.css";

type TimelineArtist = Pick<ArtistDetail, "id" | "display_name" | "timeline_start_year" | "timeline_end_year" | "timeline_display" | "timeline_basis" | "movement">;

export function ArtistArtworkTimeline({ artist, artworks, initialWorkID, undatedCount = 0, onOpenWork, onUndated }: {
  artist: TimelineArtist;
  artworks: Artwork[];
  initialWorkID?: string;
  undatedCount?: number;
  onOpenWork: (id: string) => void;
  onUndated: () => void;
}) {
  const chart = useRef<HTMLDivElement>(null);
  const markerButtons = useRef(new Map<number, HTMLButtonElement>());
  const keyboardFocus = useRef(false);
  const [width, setWidth] = useState(800);
  const [activeID, setActiveID] = useState<string>();
  // The parent supplies only its bounded gallery page and saved selections.
  // Undated works never receive an invented position on the ruler.
  const previews = [...new Map(artworks.map(work => [work.id, work])).values()]
    .sort((a, b) => (a.creation_year_start ?? Infinity) - (b.creation_year_start ?? Infinity) || a.title.localeCompare(b.title) || a.id.localeCompare(b.id));
  const entries = previews.filter(work =>
    Number.isFinite(work.creation_year_start) && work.creation_year_start !== null
    && work.date_precision !== "unknown"
    && (work.creation_year_end === null || work.creation_year_end >= work.creation_year_start)
  );
  const selected = previews.find(work => work.id === activeID)
    ?? previews.find(work => work.id === initialWorkID) ?? previews[0];
  const selectedIndex = selected ? previews.findIndex(work => work.id === selected.id) : -1;
  // A documented posthumous edition can sit beyond the life band. Never move
  // its date into the painter's lifetime to make the chart fit.
  const start = Math.min(artist.timeline_start_year, ...entries.map(work => work.creation_year_start!));
  const end = Math.max(artist.timeline_end_year, ...entries.map(work => work.creation_year_end ?? work.creation_year_start!));
  const span = Math.max(1, end - start);
  const position = (year: number) => (year - start) / span * 100;
  const slots = Math.max(1, Math.floor(width / 44));
  const grouped = new Map<number, Artwork[]>();
  for (const work of entries) {
    const slot = Math.min(slots - 1, Math.floor(position(work.creation_year_start!) / 100 * slots));
    grouped.set(slot, [...(grouped.get(slot) ?? []), work]);
  }
  const groups = [...grouped.entries()].map(([slot, works]) => ({ slot, works,
    firstYear: works[0].creation_year_start!, lastYear: works.at(-1)!.creation_year_start!,
    left: (position(works[0].creation_year_start!) + position(works.at(-1)!.creation_year_start!)) / 2,
  }));
  // Adjacent bins can meet at a boundary. Merge them when their actual centres
  // would leave overlapping touch targets, rather than displacing source dates.
  for (let index = 1; index < groups.length;) {
    const previous = groups[index - 1], current = groups[index];
    if ((current.left - previous.left) / 100 * width < 44) {
      previous.works.push(...current.works);
      previous.lastYear = current.lastYear;
      previous.left = (position(previous.firstYear) + position(previous.lastYear)) / 2;
      groups.splice(index, 1);
      index = Math.max(1, index - 1);
    } else index++;
  }
  const activeGroup = groups.find(group => group.works.some(work => work.id === selected?.id));
  const targetTicks = width < 600 ? 4 : 8;
  const rawStep = span / targetTicks;
  const magnitude = 10 ** Math.floor(Math.log10(Math.max(1, rawStep)));
  const step = [1, 2, 5, 10].map(value => value * magnitude).find(value => value >= rawStep) ?? magnitude * 10;
  const ticks: number[] = [];
  for (let year = Math.ceil(start / step) * step; year <= end; year += step) ticks.push(year);
  const isLife = artist.timeline_basis === "life";
  const hasRanges = entries.some(work => work.creation_year_end !== null && work.creation_year_end !== work.creation_year_start);
  const previewID = `artwork-timeline-preview-${artist.id}`;

  useEffect(() => {
    if (!chart.current || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(1, entry.contentRect.width)));
    observer.observe(chart.current);
    return () => observer.disconnect();
  }, []);

  function selectIndex(index: number, focus = false) {
    const work = previews[index];
    if (!work) return;
    setActiveID(work.id);
    if (focus) {
      const group = groups.find(group => group.works.some(item => item.id === work.id));
      if (group) {
        keyboardFocus.current = true;
        markerButtons.current.get(group.slot)?.focus({ preventScroll: true });
        keyboardFocus.current = false;
      }
    }
  }

  return <section className={styles.timeline} aria-labelledby={`artwork-timeline-title-${artist.id}`}
    style={{ "--artist-timeline-colour": artist.movement.color } as CSSProperties}>
    <header className={styles.heading}>
      <div><h2 id={`artwork-timeline-title-${artist.id}`}>{isLife ? "Life and artworks" : "Activity and artworks"}</h2><p>{artist.timeline_display}</p></div>
      {previews.length > 0 && <p>{previews.length} artwork {previews.length === 1 ? "preview" : "previews"}</p>}
    </header>
    <div ref={chart} className={styles.chart} role="group" aria-label={`Artwork dates for ${artist.display_name}`}>
      <div className={styles.ticks} aria-hidden="true">{ticks.map(year => <span key={year} style={{ left: `${position(year)}%` }}><span>{year}</span><i /></span>)}</div>
      <div className={styles.baseline} aria-hidden="true" />
      <div className={`${styles.lifeBand}${isLife ? "" : ` ${styles.activityBand}`}`} aria-hidden="true"
        style={{ left: `${position(artist.timeline_start_year)}%`, width: `${position(artist.timeline_end_year) - position(artist.timeline_start_year)}%` }} />
      <div className={styles.endpoints} aria-hidden="true"><span style={{ left: `${position(artist.timeline_start_year)}%` }}>{isLife ? "Born" : "From"} {artist.timeline_start_year}</span><span style={{ left: `${position(artist.timeline_end_year)}%` }}>{isLife ? "Died" : "To"} {artist.timeline_end_year}</span></div>
      {groups.map(group => {
        const active = activeGroup?.slot === group.slot;
        const date = group.firstYear === group.lastYear ? String(group.firstYear) : `${group.firstYear}–${group.lastYear}`;
        const label = `${date}: ${group.works.length} ${group.works.length === 1 ? "artwork" : "artworks"}`;
        return <button type="button" key={group.slot} className={styles.marker}
          ref={element => { if (element) markerButtons.current.set(group.slot, element); else markerButtons.current.delete(group.slot); }}
          style={{ left: `${group.left}%` }} aria-label={label} title={label}
          aria-pressed={active} aria-controls={previewID}
          onPointerEnter={event => { if (event.pointerType !== "touch" && !active) setActiveID(group.works[0].id); }}
          onFocus={() => { if (!active && !keyboardFocus.current) setActiveID(group.works[0].id); }}
          onClick={() => setActiveID(group.works[0].id)}
          onKeyDown={event => {
            const index = event.key === "ArrowLeft" ? selectedIndex - 1 : event.key === "ArrowRight" ? selectedIndex + 1 : event.key === "Home" ? 0 : event.key === "End" ? previews.length - 1 : null;
            if (index !== null) { event.preventDefault(); selectIndex(index, true); }
          }}>
          <i aria-hidden="true" />{group.works.length > 1 && <span aria-hidden="true" className={styles.clusterCount}>{group.works.length}</span>}
        </button>;
      })}
    </div>
    <div className={styles.legend}>
      <p>{entries.length ? "Select a dot to preview a work. Dots show selected works and the current gallery page." : "No dated artworks in this selection."}{hasRanges && " Ranges begin at their recorded starting year."}</p>
      {undatedCount > 0 && <button type="button" onClick={onUndated}>{undatedCount.toLocaleString("en-GB")} undated {undatedCount === 1 ? "work" : "works"}</button>}
    </div>
    {selected && <div id={previewID} className={styles.preview}>
      <button type="button" className={styles.previewImage} aria-label={`Open ${selected.title}`} onClick={() => onOpenWork(selected.id)}>
        <ArtworkImage key={selected.id} work={selected} sizes="(max-width: 600px) 90vw, 300px" />
      </button>
      <div className={styles.previewContent}>
        <div className={styles.identity} aria-live="polite" aria-atomic="true">
          <h3>{selected.title}</h3><p className={styles.date}>{artworkDate(selected) ?? "Undated"}</p>
        </div>
        {artworkMedium(selected) && <p className={styles.metadata}>{artworkMedium(selected)}</p>}
        {(selected.holding?.name || displayMetadata(selected.current_location_text)) && <p className={styles.metadata}>{selected.holding?.name || displayMetadata(selected.current_location_text)}</p>}
        <button type="button" className={styles.openWork} onClick={() => onOpenWork(selected.id)}>Open artwork <span aria-hidden="true">↗</span></button>
        <div className={styles.navigation}>
          <span>{selectedIndex + 1} of {previews.length}</span>
          <nav aria-label="Browse artwork previews">
            <button type="button" aria-label="Previous artwork preview" disabled={selectedIndex <= 0} onClick={() => selectIndex(selectedIndex - 1)}>←</button>
            <button type="button" aria-label="Next artwork preview" disabled={selectedIndex >= previews.length - 1} onClick={() => selectIndex(selectedIndex + 1)}>→</button>
          </nav>
        </div>
      </div>
    </div>}
  </section>;
}
