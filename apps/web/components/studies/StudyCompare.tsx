"use client";
import { useEffect, useState } from "react";
import { recordKey, readStudy, type StudyRecord } from "@/lib/studies";
import { StudyDialog } from "./StudyDialog";
import { RecordFacts, SourceLink, StudyImage } from "./StudyRecord";
import styles from "./Studies.module.css";

export function StudyCompare({ id, options, close, initial, shared = false }: { shared?: boolean; id: string; options: StudyRecord[]; close: () => void; initial?: string }) {
  const first = options.find(record => recordKey(record) === initial) ?? options[0];
  const [left, setLeft] = useState(recordKey(first)), [right, setRight] = useState(recordKey(options.find(record => recordKey(record) !== recordKey(first))!));
  const [records, setRecords] = useState<StudyRecord[]>([]), [error, setError] = useState(""), [loading, setLoading] = useState(true), [retry, setRetry] = useState(0);
  useEffect(() => { const controller = new AbortController(); const params = new URLSearchParams(); params.append("compare", left); params.append("compare", right); readStudy(id, params.toString(), controller.signal, shared).then(result => { setRecords(result.artworks); setLoading(false); }).catch(error => { if (!controller.signal.aborted) { setRecords([]); setError(error.message); setLoading(false); } }); return () => controller.abort(); }, [id, left, right, retry, shared]);
  return <StudyDialog title="Compare artworks" subtitle="Images fit their frames. They are not shown at relative physical scale." close={close} wide>
    {error && <p role="alert" className={styles.error}>{error} <button onClick={() => { setLoading(true); setError(""); setRetry(value => value + 1); }}>Try again</button></p>}
    {loading && <p role="status">Loading comparison…</p>}
    <div className={styles.compareGrid}>{(["left", "right"] as const).map((side, index) => { const value = side === "left" ? left : right, other = side === "left" ? right : left, record = records.find(item => recordKey(item) === value); return <section key={side}><label className={styles.compareSelect}>{index === 0 ? "First artwork" : "Second artwork"}<select aria-label={index === 0 ? "First artwork" : "Second artwork"} value={value} onChange={event => { setLoading(true); setError(""); (side === "left" ? setLeft : setRight)(event.target.value); }}>{options.map(option => <option value={recordKey(option)} key={recordKey(option)} disabled={recordKey(option) === other}>{option.title} — {option.creator}</option>)}</select></label>{record && !loading && <><StudyImage readOnly={shared} record={record} /><h3>{record.title}</h3><p>{record.creator}</p><RecordFacts record={record} /><div className={styles.sources}>{record.sources.slice(0, 3).map((source, i) => <SourceLink key={i} href={source.url}>{source.name}</SourceLink>)}</div>{record.image && <p className={styles.help}>{record.image.credit} {record.image.license}</p>}{record.note && <blockquote>{record.note}</blockquote>}</>}</section>; })}</div>
  </StudyDialog>;
}
