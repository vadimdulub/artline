"use client";
import { BookmarkButton } from "./Bookmarks";
import Link from "@/components/MemberLink";
import { artworkDate, displayMetadata } from "@/lib/display-metadata";
import { useEffect, useRef, useState } from "react";
import { safeSourceURL } from "@/lib/api";
import { lockBodyScroll } from "@/lib/modal-scroll";
import type { Museum, MuseumArtwork } from "@/lib/types";
import { ArtworkFacts } from "./ArtworkFacts";
import { ArtworkViewer, ShareWorkLink } from "./ArtworkViewer";
import { ArtworkLocation, checkedDate } from "./ArtworkLocation";
import { ArtworkDescription } from "./ArtworkDescription";
import { SourceList } from "./ArtistRecord";
import { useMuseumRequest } from "./museum-state";
import styles from "./Museums.module.css";

export function MuseumDrawer({ museum, workID, close }: { museum: Museum; workID: string; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [retry, setRetry] = useState(0);
  const { data: work, error } = useMuseumRequest<MuseumArtwork>(`museums/${museum.slug}/works/${encodeURIComponent(workID)}`, retry);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll(); element.showModal();
    return () => { element.close(); unlock(); if (focused?.isConnected) focused.focus({ preventScroll: true }); else document.getElementById("museum-results-title")?.focus({ preventScroll: true }); };
  }, []);
  return <dialog ref={dialog} className={`painter-dialog ${styles.drawer}`} aria-label="Museum artwork details" onCancel={event => { event.preventDefault(); close(); }} onClick={event => {
    if (event.target === event.currentTarget) { const rect = event.currentTarget.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) close(); }
  }}>
    <div className="dialog-toolbar artwork-dialog-toolbar"><button type="button" className="close-painter" autoFocus aria-label="Close artwork details" onClick={close}>×</button></div>
    {error ? <div className={styles.empty}><h2>Artwork unavailable</h2><p>{error}</p><button onClick={() => setRetry(value => value + 1)}>Try again</button></div> : !work ? <p className={styles.loading}>Opening artwork…</p> : <div className={styles.drawerContent}>
      <p className="artwork-creator">{work.artists.length ? work.artists.map((artist, index) => <span key={`${artist.id}-${artist.role}`}>{index > 0 && ", "}<Link href={`/artists/${artist.slug}`}>{artist.name}</Link> <BookmarkButton kind="artist" id={artist.id} title={artist.name} compact />{artist.role !== "primary" && ` (${artist.role.replaceAll("_", " ")})`}</span>) : displayMetadata(work.unlinked_creator_label)}</p>
      <ArtworkViewer key={work.id} work={work} creator={work.artists.length ? work.artists.map(artist => `${artist.name}${artist.role !== "primary" ? ` (${artist.role.replaceAll("_", " ")})` : ""}`).join(", ") : work.unlinked_creator_label} />
      <h2>{work.title}</h2><div className="bookmark-record-actions"><BookmarkButton kind="artwork" id={work.id} title={work.title} /></div>{artworkDate(work) && <p className={styles.artworkDate}>{artworkDate(work)}</p>}
      <div className={styles.badges}>{work.selections.filter(selection => selection.kind === "museum").map(selection => <span key={selection.kind}>Museum highlight</span>)}</div>
      <ShareWorkLink path={`/museums/${museum.slug}?work=${work.id}`} />
      <div className="artwork-details"><ArtworkFacts work={work} /></div>
      <p className="image-credit">{work.attribution_text}</p>
      <ArtworkLocation work={work} />
      <ArtworkDescription key={work.id} work={work} detailPath={`museums/${museum.slug}/works/${work.id}`} />
      {work.location_checked_at && <p className={styles.note}>Holding record checked {checkedDate(work.location_checked_at)}. This is not a current display check.</p>}
      {work.selections.filter(selection => selection.kind === "museum").map(selection => <section key={selection.kind} className={styles.selectionNote}><h3>Why this is a museum highlight</h3>{selection.reason && <p>{selection.reason}</p>}{selection.source_url && <a href={safeSourceURL(selection.source_url)} target="_blank" rel="noreferrer">Designation source{selection.checked_at ? ` · checked ${checkedDate(selection.checked_at)}` : ""}</a>}</section>)}
      {(work.citations.length > 0 || safeSourceURL(work.source_page_url)) && <details className="sources-section"><summary>Artwork sources</summary><SourceList citations={work.citations} />{safeSourceURL(work.source_page_url) && <a href={safeSourceURL(work.source_page_url)} target="_blank" rel="noreferrer">Image source</a>}</details>}
    </div>}
  </dialog>;
}
