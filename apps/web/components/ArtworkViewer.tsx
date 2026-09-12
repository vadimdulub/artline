"use client";
import { lockBodyScroll } from "@/lib/modal-scroll";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import type { Artwork } from "@/lib/types";
import { fitImage, imageZoomLevels } from "@/lib/image-view";

function ZoomableArtwork({ work }: { work: Artwork }) {
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
  return <div className="image-viewer" onKeyDown={event => {
    if (!ready || event.ctrlKey || event.metaKey || event.altKey) return;
    if (["+", "=", "-", "0"].includes(event.key)) { event.preventDefault(); changeZoom(event.key === "0" ? 0 : level + (event.key === "-" ? -1 : 1)); }
  }}>
    <div className="image-zoom-controls" role="group" aria-label="Image zoom">
      <button type="button" aria-label="Zoom out" disabled={!ready || level === 0} onClick={() => changeZoom(level - 1)}>−</button>
      <output aria-live="polite" aria-label="Image magnification">{level === 0 ? "Fit" : `${zoom}× fit`}</output>
      <button type="button" aria-label="Zoom in" disabled={!ready || level === imageZoomLevels.length - 1} onClick={() => changeZoom(level + 1)}>+</button>
      <button type="button" className="fit-image" disabled={!ready || level === 0} onClick={() => changeZoom(0)}>Fit image</button>
    </div>
    <div ref={stage} className="image-dialog-stage" tabIndex={0} role="region" aria-label={`Image detail: ${work.title}`} aria-describedby="image-viewer-help">
      {failed ? <div className="image-load-error" role="alert"><p>The full-size image couldn’t load.</p><button type="button" onClick={() => { setFailed(false); setAttempt(value => value + 1); }}>Retry image</button></div> : <div className="image-scroll-canvas" style={{ width: ready ? Math.max(viewport.width, fit.width * zoom) : "100%", height: ready ? Math.max(viewport.height, fit.height * zoom) : "100%" }}>
        {/* Load the original local file only when opened, retaining detail at every zoom level. */}
        <Image key={attempt} unoptimized src={work.media_url!} alt={work.alt_text ?? work.title} width={natural.width || 1600} height={natural.height || 1600} loading="eager" onLoad={event => setNatural({ width: event.currentTarget.naturalWidth, height: event.currentTarget.naturalHeight })} onError={() => setFailed(true)} style={{ width: ready ? fit.width * zoom : "100%", height: ready ? fit.height * zoom : "100%" }} />
      </div>}
    </div>
    <p className="image-viewer-help" id="image-viewer-help">{level === 0 ? "Zoom in for a closer look." : "Scroll to explore the enlarged image."} <span>Keyboard: + / − to zoom, 0 to fit; arrow keys scroll the focused image.</span></p>
  </div>;
}

export function permittedImagePath(path: string | null) {
  return Boolean(path && /^\/assets\/[a-zA-Z0-9/_-]+\.(jpg|jpeg|png|webp|avif)$/.test(path) && !path.includes(".."));
}

export function ArtworkImage({ work, large = false, number, onUnavailable }: { work: Pick<Artwork, "media_url" | "alt_text" | "title" | "rights_status">; large?: boolean; number?: number; onUnavailable?: () => void }) {
  const [failed, setFailed] = useState(false);
  const usable = permittedImagePath(work.media_url) && !failed;
  if (usable) return <Image src={work.media_url!} alt={work.alt_text ?? ""} loading={large ? "eager" : "lazy"} width={large ? 1600 : 440} height={large ? 1600 : 520} sizes={large ? "(max-width: 760px) 90vw, 55vw" : number !== undefined ? "100px" : "(max-width: 620px) 45vw, 25vw"} onError={() => { setFailed(true); onUnavailable?.(); }} />;
  if (number !== undefined && !large) return <div className="work-placeholder numbered-placeholder"><span aria-hidden="true">{String(number).padStart(2, "0")}</span><span className="sr-only">{failed ? "Image unavailable" : "Image not available"}</span></div>;
  return <div className={large ? "work-placeholder large-placeholder" : "work-placeholder"}><span aria-hidden="true">▧</span><p>{failed ? "Image unavailable" : "Image not available"}</p>{large && <small>{work.rights_status === "restricted" ? "Reproduction rights are restricted." : "You can still explore the artwork’s details and sources below."}</small>}</div>;
}

export function ArtworkViewer({ work }: { work: Artwork }) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (!open || !element) return;
    const focused = document.activeElement as HTMLElement | null;
    const unlock = lockBodyScroll();
    element.showModal();
    return () => { element.close(); unlock(); focused?.focus({ preventScroll: true }); };
  }, [open]);
  return <>
    <figure className="artwork-image"><ArtworkImage work={work} large onUnavailable={() => setFailed(true)} />{permittedImagePath(work.media_url) && !failed && <button type="button" className="enlarge-image" onClick={() => setOpen(true)}>View larger <span aria-hidden="true">⤢</span></button>}</figure>
    {open && <dialog ref={dialog} className="image-dialog" aria-label={`Enlarged image: ${work.title}`} onCancel={event => { event.preventDefault(); event.stopPropagation(); setOpen(false); }}><header><div><h2>{work.title}</h2><p>{work.date_display}</p></div><button autoFocus type="button" aria-label="Close enlarged image" onClick={() => setOpen(false)}>×</button></header><ZoomableArtwork work={work} /><p className="image-dialog-credit">{work.attribution_text ?? work.license_label}</p></dialog>}
  </>;
}

export function ShareWorkLink({ path }: { path: string }) {
  const [copied, setCopied] = useState(false);
  const [fallback, setFallback] = useState("");
  const fallbackInput = useRef<HTMLInputElement>(null);
  useEffect(() => { if (fallback) { fallbackInput.current?.focus(); fallbackInput.current?.select(); } }, [fallback]);
  async function copy() {
    const url = new URL(path, window.location.origin).href;
    setCopied(false);
    try { await navigator.clipboard.writeText(url); setCopied(true); setFallback(""); }
    catch { setFallback(url); fallbackInput.current?.focus(); fallbackInput.current?.select(); }
  }
  return <div className="share-work"><button type="button" onClick={() => void copy()}>{copied ? "Link copied" : "Copy artwork link"}</button><span role="status" className="sr-only">{copied ? "Artwork link copied to clipboard." : fallback ? "Automatic copying is unavailable. The link is selected for you to copy." : ""}</span>{fallback && <label><span>Copy this artwork link</span><input ref={fallbackInput} readOnly value={fallback} onFocus={event => event.currentTarget.select()} /></label>}</div>;
}
