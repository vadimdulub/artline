"use client";
import { useEffect, useRef, useState } from "react";
import { recordKey, yearLabel, type StudyInterval, type StudyRecord } from "@/lib/studies";
import { StudyImage } from "./StudyRecord";
import styles from "./Studies.module.css";

export function StudyTimeline({ records, range, selected, select, readOnly = false }: { readOnly?: boolean; records: StudyRecord[]; range: StudyInterval | null; selected?: string; select: (record: StudyRecord) => void }) {
  const container = useRef<HTMLDivElement>(null);
  const [availableWidth, setAvailableWidth] = useState(1000);
  useEffect(() => { const observer = new ResizeObserver(entries => setAvailableWidth(entries[0].contentRect.width)); if (container.current) observer.observe(container.current); return () => observer.disconnect(); }, []);
  const dated = records.filter(record => record.intervals.length), undated = records.filter(record => !record.intervals.length);
  const start = range ? range.start - (range.start === range.end ? 2 : 0) : 1800, end = range ? range.end + (range.start === range.end ? 2 : 0) : 1900;
  const span = Math.max(1, end - start), tail = 242, plotWidth = Math.max(400, availableWidth - 176 - tail);
  const position = (year: number) => Math.max(0, Math.min(plotWidth, (year - start) / span * plotWidth));
  const ticks = Array.from({ length: 6 }, (_, index) => Math.round(start + index * span / 5)).filter((year, index, values) => year !== 0 && values.indexOf(year) === index);
  return <div className={styles.timelineArea} ref={container}>
    {dated.length > 0 && <div className={styles.timelineScroll} tabIndex={0} role="region" aria-label="Study timeline. Scroll horizontally to explore dates."><div className={styles.timelineCanvas} style={{ width: 176 + plotWidth + tail }}>
      <div className={styles.timelineAxis}><span>People & context</span><div style={{ width: plotWidth + tail }}>{ticks.map(year => <span style={{ left: position(year) }} key={year}>{yearLabel(year)}</span>)}</div></div>
      {dated.map(record => { const intervals = record.intervals.filter(interval => !range || interval.start <= range.end && interval.end >= range.start); return <div className={styles.timelineRow} key={recordKey(record)}><div className={styles.rowLabel}><strong>{record.creator || (record.kind === "event" ? "Historical context" : "Creator not recorded")}</strong><span>{record.kind === "artwork" ? "Artwork" : record.kind === "book" ? "Book" : "Event"}</span></div><div className={styles.rowPlot} style={{ width: plotWidth + tail }}>{ticks.map(year => <span className={styles.gridLine} style={{ left: position(year) }} key={year} />)}<button className={styles.timelineCard} data-kind={record.kind} aria-pressed={selected === recordKey(record)} style={{ left: position((intervals[0] ?? record.intervals[0]).start) }} onClick={() => select(record)}><StudyImage readOnly={readOnly} small record={record} /><span><strong>{record.title}</strong><span>{record.date || "Date not recorded"}</span>{record.personal && <small>{readOnly ? "Personal record" : "Your own"}</small>}</span></button><div className={styles.intervals}>{intervals.map((interval, index) => <span className={styles.interval} key={index} data-point={interval.start === interval.end} data-kind={record.kind} title={`${yearLabel(interval.start)}${interval.start !== interval.end ? `–${yearLabel(interval.end)}` : ""}`} style={{ left: position(interval.start), width: Math.max(5, position(interval.end) - position(interval.start)) }} />)}</div></div></div>; })}
    </div></div>}
    {undated.length > 0 && <section className={styles.undated}><h3>Undated & qualified dates</h3><p>These records remain in the study. A closed date interval has not been established.</p><div className={styles.undatedCards}>{undated.map(record => <button key={recordKey(record)} aria-pressed={selected === recordKey(record)} onClick={() => select(record)}><strong>{record.title}</strong><span>{record.creator}</span><small>{record.date || "Date not recorded"}{record.personal ? readOnly ? " · Personal record" : " · Your own" : ""}</small></button>)}</div></section>}
    <p className={styles.timelineFootnote}>Dates follow the recorded evidence. A shared period suggests a comparison; it does not establish influence.</p>
  </div>;
}
