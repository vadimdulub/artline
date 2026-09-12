"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { apiRequest, editorHeaders, errorMessage, safeSourceURL } from "@/lib/api";
import { lockBodyScroll } from "@/lib/modal-scroll";
import type { Museum, MuseumArtwork } from "@/lib/types";
import { ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { ArtworkLocation, checkedDate } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { SourceList } from "./ArtistRecord";
import { useMuseumRequest } from "./museum-state";
import styles from "./Museums.module.css";

function MustSeeEditor({ museum, work, token, saved, reload, dirty, busy }: { museum: Museum; work: MuseumArtwork; token: string; saved: () => void; reload: () => void; dirty: (value: boolean) => void; busy: (value: boolean) => void }) {
  const current = work.selections.find(selection => selection.kind === "owner");
  const [selected, setSelected] = useState(Boolean(current));
  const [reason, setReason] = useState(current?.reason ?? "");
  const [position, setPosition] = useState(String(current?.position ?? museum.must_see_count + 1));
  const [saving, setSaving] = useState(false), [error, setError] = useState("");
  async function save() {
    setSaving(true); busy(true); setError("");
    try {
      await apiRequest(`museums/${museum.slug}/must-see`, { method: "PATCH", headers: editorHeaders(token), body: JSON.stringify({ artwork_id: work.id, selected, position: Number(position), reason, expected_revision: museum.owner_revision }) });
      dirty(false); saved();
    } catch (error) { setError(errorMessage(error)); } finally { setSaving(false); busy(false); }
  }
  return <form className={styles.mustSeeEditor} onSubmit={event => { event.preventDefault(); void save(); }}>
    <h3>My must-see selection</h3><p>Your selection is separate from the museum’s highlights. Changes remain in review.</p>
    <fieldset disabled={saving}><legend className="sr-only">Edit must-see selection</legend>
      <label className={styles.check}><input type="checkbox" checked={selected} onChange={event => { setSelected(event.target.checked); dirty(true); }} /><span>Include in my must-see works</span></label>
      {selected && <><label><span>Why I want to see it</span><textarea value={reason} maxLength={2000} onChange={event => { setReason(event.target.value); dirty(true); }} /></label><label><span>Order in my selection</span><input type="number" min={1} max={100000} step={1} required value={position} onChange={event => { setPosition(event.target.value); dirty(true); }} /></label></>}
      <button type="submit">{saving ? "Saving…" : "Save my selection"}</button>
    </fieldset>
    {error && <div role="alert"><p>{error}</p><button type="button" onClick={() => { if (window.confirm("Reload the saved selection and discard these unsaved changes?")) { dirty(false); reload(); } }}>Reload saved selection</button></div>}
  </form>;
}

export function MuseumDrawer({ museum, workID, token, revision, close, saved, reload, editAccess }: { museum: Museum; workID: string; token: string; revision: number; close: () => void; saved: () => void; reload: () => void; editAccess: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [dirty, setDirty] = useState(false), [retry, setRetry] = useState(0);
  const [busy, setBusy] = useState(false), [saveMessage, setSaveMessage] = useState("");
  const { data: work, error } = useMuseumRequest<MuseumArtwork>(`museums/${museum.slug}/works/${encodeURIComponent(workID)}`, token, revision + retry);
  function dismiss() { if (!busy && (!dirty || window.confirm("Discard your unsaved must-see changes?"))) close(); }
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll(); element.showModal();
    return () => { element.close(); unlock(); if (focused?.isConnected) focused.focus({ preventScroll: true }); else document.getElementById("museum-results-title")?.focus({ preventScroll: true }); };
  }, []);
  useEffect(() => {
    if (!dirty) return;
    function warn(event: BeforeUnloadEvent) { event.preventDefault(); }
    window.addEventListener("beforeunload", warn); return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  return <dialog ref={dialog} className={`painter-dialog ${styles.drawer}`} aria-label="Museum artwork details" onCancel={event => { event.preventDefault(); dismiss(); }} onClick={event => {
    if (event.target === event.currentTarget) { const rect = event.currentTarget.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dismiss(); }
    if (event.target instanceof Element && event.target.closest("a") && (busy || (dirty && !window.confirm("Leave this record and discard your unsaved changes?")))) event.preventDefault();
  }}>
    <div className="dialog-toolbar"><span>{busy ? "Saving selection…" : "Artwork record"}</span><button type="button" className="close-painter" disabled={busy} autoFocus aria-label="Close artwork details" onClick={dismiss}>×</button></div>
    <p role="status" className={styles.saveStatus}>{saveMessage}</p>
    {error ? <div className={styles.empty}><h2>Artwork unavailable</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : !work ? <p className={styles.loading}>Opening artwork record…</p> : <div className={styles.drawerContent}>
      <p className={styles.place}>{work.artists.length ? work.artists.map((artist, index) => <span key={`${artist.id}-${artist.role}`}>{index > 0 && ", "}<Link href={`/artists/${artist.slug}`}>{artist.name}</Link>{artist.role !== "primary" && ` (${artist.role.replaceAll("_", " ")})`}</span>) : work.unlinked_creator_label ?? "Creator not recorded"}</p>
      <h2>{work.title}</h2><p className={styles.artworkDate}>{work.date_display}</p>
      <div className={styles.badges}>{work.selections.map(selection => <span key={selection.kind}>{selection.kind === "owner" ? "My must-see work" : "Museum highlight"}</span>)}</div>
      <ArtworkViewer key={work.id} work={work} />
      <ShareWorkLink path={`/museums/${museum.slug}?work=${work.id}`} />
      <div className="artwork-details"><dl>
        <div><dt>Dating</dt><dd>{work.date_precision.replaceAll("_", " ")}</dd></div>
        {work.object_form && <div><dt>Object form</dt><dd>{work.object_form}</dd></div>}
        {work.cultural_context && <div><dt>Tradition / school</dt><dd>{work.cultural_context}</dd></div>}
        <div><dt>Made in</dt><dd>{work.creation_place_display ?? "Not established"}{!work.creation_place_display && <small className="metadata-note">{work.creation_place_unknown_reason}</small>}</dd></div>
        <div><dt>Held at</dt><dd>{work.holding ? <Link href={`/museums/${work.holding.slug}`}>{work.holding.name}</Link> : work.current_location_text ?? "Location under review"}</dd></div>
        <div><dt>Medium</dt><dd>{work.medium_text ?? work.work_type.replaceAll("_", " ")}</dd></div>
        <div><dt>Dimensions</dt><dd>{work.dimensions_text ?? "Not recorded"}</dd></div>
        {work.accession_number && <div><dt>Collection no.</dt><dd>{work.accession_number}</dd></div>}
        <div><dt>Image rights</dt><dd>{work.license_label ?? work.rights_status ?? "Not reviewed"}{safeSourceURL(work.license_url) && <a className="license-link" href={safeSourceURL(work.license_url)} target="_blank" rel="noreferrer">License details</a>}</dd></div>
      </dl></div>
      <p className="image-credit">{work.attribution_text}</p>
      <ArtworkLocation work={work} />
      <ArtworkDescription key={work.id} work={work} detailPath={`museums/${museum.slug}/works/${work.id}`} token={token} />
      {work.location_checked_at && <p className={styles.note}>Holding record checked {checkedDate(work.location_checked_at)}. This is not a current display check.</p>}
      {work.selections.map(selection => <section key={selection.kind} className={styles.selectionNote}><h3>{selection.kind === "owner" ? "My must-see note" : "Why this is a museum highlight"}</h3><p>{selection.reason || "Selected for my personal list."}</p>{selection.source_url && <a href={safeSourceURL(selection.source_url)} target="_blank" rel="noreferrer">Designation source{selection.checked_at ? ` · checked ${checkedDate(selection.checked_at)}` : ""}</a>}</section>)}
      <details className="sources-section"><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>
      {token ? <MustSeeEditor key={`${work.id}-${revision}-${retry}`} museum={museum} work={work} token={token} dirty={setDirty} busy={setBusy} saved={() => { setSaveMessage("Your must-see selection was saved in review."); saved(); }} reload={() => { setSaveMessage("Unsaved changes discarded. Requesting the saved selection…"); reload(); }} /> : <div className={styles.selectionNote}><h3>Make this atlas yours</h3><p>Add this artwork to your personal must-see selection with editor access.</p><button onClick={editAccess}>Edit my must-see list</button></div>}
    </div>}
  </dialog>;
}
