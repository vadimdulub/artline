"use client";
import { BookmarkButton } from "./Bookmarks";
import { artworkDate, displayMetadata } from "@/lib/display-metadata";
import { lockBodyScroll } from "@/lib/modal-scroll";
import Image from "next/image";
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { Artwork } from "@/lib/types";
import { RecordArrows, type RecordNavigation } from "./RecordNavigation";
import { fitImage, imageZoomLevels } from "@/lib/image-view";
import { ArtworkPalette } from "./ArtworkPalette";
import styles from "./ArtworkViewer.module.css";

function ZoomableArtwork({ work, detailsControl }: { work: Artwork; detailsControl: ReactNode }) {
  const stage = useRef<HTMLDivElement>(null);
  const [viewport, setViewport] = useState({ width: 0, height: 0 });
  const [natural, setNatural] = useState({ width: 0, height: 0 });
  const [level, setLevel] = useState(0);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const center = useRef({ x: 0.5, y: 0.5 });
  const zoom = imageZoomLevels[level];
  const fit = fitImage(natural.width, natural.height, viewport.width, viewport.height);
  const ready = fit.width > 0 && !failed;
  const zoomed = ready && level > 0;
  useEffect(() => {
    if (!stage.current) return;
    const observer = new ResizeObserver(([entry]) => setViewport({ width: entry.contentRect.width, height: entry.contentRect.height }));
    observer.observe(stage.current);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    const element = stage.current;
    if (!element) return;
    element.scrollTo({ left: center.current.x * element.scrollWidth - element.clientWidth / 2, top: center.current.y * element.scrollHeight - element.clientHeight / 2, behavior: "instant" });
  }, [level, fit.width, fit.height]);
  function changeZoom(next: number) {
    const element = stage.current;
    if (element) center.current = { x: (element.scrollLeft + element.clientWidth / 2) / element.scrollWidth, y: (element.scrollTop + element.clientHeight / 2) / element.scrollHeight };
    if (next === 0) center.current = { x: 0.5, y: 0.5 };
    setLevel(Math.max(0, Math.min(imageZoomLevels.length - 1, next)));
  }
  return <div className={`image-viewer ${styles.viewer}`} onKeyDown={event => {
    if ((event.target as HTMLElement).closest("input, select, textarea")) return;
    if (!ready || event.ctrlKey || event.metaKey || event.altKey) return;
    if (["+", "=", "-", "0"].includes(event.key)) { event.preventDefault(); changeZoom(event.key === "0" ? 0 : level + (event.key === "-" ? -1 : 1)); }
  }}>
    <div ref={stage} className="image-dialog-stage" tabIndex={0} role="region" aria-label={`Image detail: ${work.title}`} aria-describedby="image-viewer-help">
      {failed ? <div className="image-load-error" role="alert"><p>Image not available</p><button type="button" onClick={() => { setFailed(false); setAttempt(value => value + 1); }}>Retry image</button></div> : <div className={`image-scroll-canvas${zoomed ? "" : " is-fit"}`} style={zoomed ? { width: Math.max(viewport.width, fit.width * zoom), height: Math.max(viewport.height, fit.height * zoom) } : undefined}>
        {/* Load the original local file only when opened, retaining detail at every zoom level. */}
        <Image key={attempt} unoptimized src={work.media_url!} alt={work.alt_text ?? work.title} width={natural.width || 1600} height={natural.height || 1600} loading="eager" onLoad={event => setNatural({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} onError={() => setFailed(true)} style={ready ? { width: fit.width * zoom, height: fit.height * zoom } : undefined} />
      </div>}
    </div>
    <p className="sr-only" id="image-viewer-help">{level === 0 ? "Zoom in for a closer look." : "Scroll to explore the enlarged image."} Keyboard: + / − to zoom, 0 to fit; arrow keys scroll the focused image.</p>
    <div className={styles.controls}>
    <div className="image-zoom-controls" role="group" aria-label="Image zoom">
      <button type="button" aria-label="Zoom out" disabled={!ready || level === 0} onClick={() => changeZoom(level - 1)}>−</button>
      <output aria-live="polite" aria-label="Image magnification">{level === 0 ? "Fit" : `${zoom}× fit`}</output>
      <button type="button" aria-label="Zoom in" disabled={!ready || level === imageZoomLevels.length - 1} onClick={() => changeZoom(level + 1)}>+</button>
      <button type="button" className="fit-image" disabled={!ready || level === 0} onClick={() => changeZoom(0)} aria-label="Fit image">Fit</button>
    </div>
      <div className={styles.colors}>{ready && <ArtworkPalette src={work.media_url!} dark />}</div>
      {detailsControl}
    </div>
  </div>;
}

export function permittedImagePath(path: string | null) {
  return Boolean(path && /^\/assets\/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$/.test(path) && !path.includes(".."));
}

export function ArtworkImage({ work, large = false, eager = false, number, onUnavailable, sizes }: { work: Pick<Artwork, "media_url" | "alt_text" | "title" | "rights_status">; large?: boolean; eager?: boolean; number?: number; onUnavailable?: () => void; sizes?: string }) {
  const [failedSource, setFailedSource] = useState<string | null>(null);
  const usable = permittedImagePath(work.media_url) && work.media_url !== failedSource;
  // Catalogue reproductions are already sized for delivery. Reusing the same
  // asset avoids an optimizer round trip and width-specific duplicate downloads.
  if (usable) return <Image unoptimized src={work.media_url!} alt={work.alt_text || work.title} loading={large || eager ? "eager" : "lazy"} decoding="async" width={large ? 1600 : 440} height={large ? 1600 : 520} sizes={sizes ?? (large ? "(max-width: 760px) 90vw, 55vw" : number !== undefined ? "100px" : "(max-width: 620px) 45vw, 25vw")} onError={() => { setFailedSource(work.media_url); onUnavailable?.(); }} />;
  return <div className={`work-placeholder image-unavailable${large ? " large-placeholder" : ""}`}><p>Image not available</p></div>;
}

export function ArtworkViewer({ work, navigation, creator }: { work: Artwork; navigation?: RecordNavigation; creator?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [failedID, setFailedID] = useState("");
  return <>
    <figure className="artwork-image"><ArtworkImage key={work.id} work={work} large onUnavailable={() => setFailedID(work.id)} />{permittedImagePath(work.media_url) && failedID !== work.id && <button type="button" className="enlarge-image" onClick={() => setOpen(true)}>View larger <span aria-hidden="true">⤢</span></button>}</figure>
    {open && <ArtworkDialog work={work} creator={creator} navigation={navigation} close={() => setOpen(false)} />}
  </>;
}

export function ArtworkDialog({ work, navigation, creator, close, details }: { work: Artwork; navigation?: RecordNavigation; creator?: ReactNode; close: () => void; details?: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll();
    element.showModal();
    return () => { element.close(); unlock(); focused?.focus({ preventScroll: true }); };
  }, []);
  const detailsControl = <footer className={`image-dialog-caption ${styles.caption}`}>
    <details key={work.id} className={`image-dialog-details ${styles.details}`} onKeyDown={event => {
      if (event.key === "Escape" && event.currentTarget.open) {
        event.preventDefault(); event.stopPropagation(); event.currentTarget.open = false;
        event.currentTarget.querySelector("summary")?.focus({ preventScroll: true });
      }
    }}>
      <summary aria-label="Artwork details and sources">Details</summary>
      <div className={styles.detailPanel}>
        <div className="bookmark-title"><strong>{work.title}</strong><BookmarkButton kind="artwork" id={work.id} title={work.title} /></div>
        <p>{creator ?? displayMetadata(work.unlinked_creator_label)}</p>
        {artworkDate(work) && <p>{artworkDate(work)}</p>}
        <p>{[work.medium_text, work.current_location_text].filter(Boolean).join(" · ")}</p>
        {details && <div className="artwork-details">{details}</div>}
        <p className="image-dialog-credit">{work.attribution_text ?? work.license_label}</p>
        {permittedImagePath(work.media_url) && <p className={styles.keyboardHelp}>Keyboard: + / − to zoom, 0 to fit. Arrow keys scroll the focused image.</p>}
      </div>
    </details>
  </footer>;
  return <dialog ref={dialog} className={`image-dialog ${styles.dialog}`} aria-label={`Enlarged image: ${work.title}`} onCancel={event => { event.preventDefault(); event.stopPropagation(); close(); }}>
      <header className={`image-dialog-toolbar ${styles.header}`}>
        <div className={styles.identity}><h2 title={work.title} aria-live="polite">{work.title}</h2><p className="image-dialog-artist">{creator ?? displayMetadata(work.unlinked_creator_label)}</p></div>
        {navigation && <RecordArrows navigation={navigation} noun="artwork" />}
        <button autoFocus type="button" aria-label="Close enlarged image" onClick={close}>×</button>
      </header>
      {permittedImagePath(work.media_url) ? <ZoomableArtwork key={work.id} work={work} detailsControl={detailsControl} /> : <div className={`image-viewer ${styles.viewer} ${styles.unavailableViewer}`}><div className={styles.unavailableStage}><p role="status">Image not available</p></div><div className={styles.unavailableControls}>{detailsControl}</div></div>}
    </dialog>;
}

export function ShareWorkLink({ path }: { path: string }) {
  const [copiedPath, setCopiedPath] = useState("");
  const copied = copiedPath === path;
  const [fallback, setFallback] = useState("");
  const fallbackInput = useRef<HTMLInputElement>(null);
  useEffect(() => { if (fallback) { fallbackInput.current?.focus(); fallbackInput.current?.select(); } }, [fallback]);
  async function copy() {
    const url = new URL(path, window.location.origin).href;
    setCopiedPath("");
    try { await navigator.clipboard.writeText(url); setCopiedPath(path); setFallback(""); }
    catch { setFallback(url); fallbackInput.current?.focus(); fallbackInput.current?.select(); }
  }
  return <div className="share-work"><button type="button" className={`share-work-button${copied ? " is-copied" : ""}`} onClick={() => void copy()}>
    <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{copied ? <path d="m5 12 4 4L19 6" /> : <><path d="M10 13a5 5 0 0 0 7.1 0l3-3a5 5 0 0 0-7.1-7.1l-1.7 1.7" /><path d="M14 11a5 5 0 0 0-7.1 0l-3 3a5 5 0 0 0 7.1 7.1l1.7-1.7" /></>}</svg>
    <span>{copied ? "Link copied" : "Copy artwork link"}</span>
  </button><span role="status" className="sr-only">{copied ? "Artwork link copied to clipboard." : fallback ? "Automatic copying is unavailable. The link is selected for you to copy." : ""}</span>{fallback && <label><span>Copy this artwork link</span><input ref={fallbackInput} readOnly value={fallback} onFocus={event => event.currentTarget.select()} /></label>}</div>;
}
