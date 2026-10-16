"use client";
/* eslint-disable @next/next/no-img-element -- Source-linked catalogue reproductions retain their approved URLs. */
import Link from "next/link";
import { useState } from "react";
import { safeStudyLink, type StudyRecord as RecordData } from "@/lib/studies";
import { NavigationIcon } from "@/components/MemberNavigation";
import styles from "./Studies.module.css";

export function StudyImage({ record, small = false, readOnly = false }: { record: RecordData; small?: boolean; readOnly?: boolean }) {
  const [failed, setFailed] = useState(false);
  return <div className={`${styles.image} ${small ? styles.smallImage : ""}`}>{record.image && !failed ? <img src={record.image.imageUrl} alt={record.image.label || record.title} loading="lazy" onError={() => setFailed(true)} /> : <span className={styles.imagePlaceholder}><NavigationIcon kind={record.kind === "artwork" ? "artworks" : record.kind === "book" ? "guide" : "about"} /><span>{record.personal ? readOnly ? "Personal record" : "Your own" : failed ? "Image unavailable" : "No image recorded"}</span></span>}</div>;
}
export function SourceLink({ href, children }: { href: string; children: React.ReactNode }) { const safe = safeStudyLink(href); return safe ? <a href={safe} target="_blank" rel="noopener noreferrer">{children} <span aria-hidden>↗</span></a> : null; }
export function RecordFacts({ record }: { record: RecordData }) { return <dl className={styles.facts}><dt>Date</dt><dd>{record.date || "Not recorded"}</dd>{record.medium && <><dt>Medium</dt><dd>{record.medium}</dd></>}{record.dimensions && <><dt>Dimensions</dt><dd>{record.dimensions}</dd></>}{record.holding && <><dt>Held at</dt><dd>{record.holding}</dd></>}</dl>; }
export function RecordInspector({ record, saveNote, remove, busy, close, readOnly = false }: { readOnly?: boolean; record: RecordData; saveNote: (note: string) => Promise<void>; remove: () => Promise<void>; busy: boolean; close: () => void }) {
  const [note, setNote] = useState(record.note), [message, setMessage] = useState(""), [error, setError] = useState(""), [confirm, setConfirm] = useState(false);
  const dirty = note !== record.note;
  const sources = record.sources.filter((source, index, all) => all.findIndex(v => v.url === source.url) === index);
  return <section className={styles.inspector} aria-label="Record inspection">
    <div className={styles.inspectorTop}><span>{record.personal ? readOnly ? "Personal record" : "Your own" : record.kind === "artwork" ? "Artwork" : record.kind === "book" ? "Book" : "Event"}</span><button className={styles.iconButton} aria-label="Close record" onClick={close}>×</button></div>
    <StudyImage readOnly={readOnly} record={record} /><h2>{record.title}</h2><p className={styles.creator}>{record.creator || "Creator not recorded"}</p><RecordFacts record={record} />
    <div className={styles.sources}>{sources.length ? sources.slice(0, 2).map(source => <SourceLink key={source.url} href={source.url}>{source.name || "View source record"}</SourceLink>) : <p>No external source link recorded.</p>}<SourceLink href={record.href}>{record.personal ? readOnly ? "Open source" : "Open your source" : "Open catalogue record"}</SourceLink></div>
    {readOnly ? record.note && <div className={styles.readOnlyNote}><h3>Research note</h3><p>{record.note}</p></div> : <form className={styles.noteForm} onSubmit={async event => { event.preventDefault(); setError(""); setMessage(""); try { await saveNote(note); setMessage("Note saved."); } catch (error) { setError(error instanceof Error ? error.message : "Your note could not be saved."); } }}><label htmlFor="study-note">Your note</label><textarea id="study-note" rows={5} maxLength={4000} value={note} placeholder="Record an observation or a question to investigate…" onChange={event => { setNote(event.target.value); setMessage(""); }} /><div><span className={styles.help}>{note.length}/4,000</span><button type="submit" disabled={busy || !dirty}>{busy ? "Saving…" : "Save note"}</button></div><p role="status">{message || (dirty ? "Unsaved changes" : "")}</p></form>}
    {error && <p role="alert" className={styles.error}>{error}</p>}
    <details className={styles.disclosure}><summary>Date & source notes</summary><p>{record.date_note}</p>{sources.slice(2).map(source => <p key={source.url}><SourceLink href={source.url}>{source.name}</SourceLink></p>)}<p>{record.personal ? "Personal reference added" : "Catalogue snapshot captured"} {new Date(record.captured_at).toLocaleDateString()}. {record.holding && "Holdings do not establish current display or loan availability."}</p></details>
    {record.image && <details className={styles.disclosure}><summary>Image credit</summary>{record.image.artwork && <p><Link href={record.image.artwork.href} prefetch={false}>{record.image.artwork.title}</Link></p>}<p>{record.image.credit || "Credit not recorded"}</p><p>{record.image.license || "Rights label not recorded"}</p><SourceLink href={record.image.sourceUrl}>Image source</SourceLink>{record.image.licenseUrl && <SourceLink href={record.image.licenseUrl}>Rights information</SourceLink>}</details>}
    {!readOnly && (confirm ? <div className={styles.removeConfirm}><p>Remove this record and its note from this study?</p><button disabled={busy} onClick={async () => { try { await remove(); } catch (error) { setError(error instanceof Error ? error.message : "Couldn’t remove this record."); } }}>Remove record</button><button onClick={() => setConfirm(false)}>Keep record</button></div> : <button className={styles.textButton} onClick={() => setConfirm(true)}>Remove from study</button>)}
  </section>;
}
