"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { extractPalette, sampleArtworkImage } from "@/lib/artwork-palette";
import styles from "./ArtworkPalette.module.css";

export function ArtworkPalette({ src, dark = false }: { src: string; dark?: boolean }) {
  // The inner key discards pending results and copied values when navigating works.
  return <Palette key={src} src={src} dark={dark} />;
}

function Palette({ src, dark }: { src: string; dark: boolean }) {
  const [attempt, setAttempt] = useState(0);
  const [sample, setSample] = useState<Uint8ClampedArray | null>(null);
  const [failed, setFailed] = useState(false);
  const [copied, setCopied] = useState("");
  const [manual, setManual] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const selectedButton = useRef<HTMLButtonElement | null>(null);
  const copyRequest = useRef(0);
  const palette = useMemo(() => sample ? extractPalette(sample, 8) : [], [sample]);
  useEffect(() => {
    if (sample) return;
    const controller = new AbortController();
    sampleArtworkImage(src, controller.signal).then(pixels => {
      if (!controller.signal.aborted) setSample(pixels);
    }).catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, [src, sample, attempt]);
  useEffect(() => { if (manual) { input.current?.focus({ preventScroll: true }); input.current?.select(); } }, [manual]);
  useEffect(() => {
    if (!copied) return;
    const timeout = window.setTimeout(() => setCopied(""), 4000);
    return () => window.clearTimeout(timeout);
  }, [copied]);
  useEffect(() => () => { copyRequest.current++; }, []);
  async function copy(hex: string) {
    const request = ++copyRequest.current;
    setCopied(""); setManual("");
    try {
      await navigator.clipboard.writeText(hex);
      if (request === copyRequest.current) setCopied(hex);
    } catch { if (request === copyRequest.current) setManual(hex); }
  }
  return <div className={`${styles.palette}${dark ? ` ${styles.dark}` : ""}`} role="group" aria-label="Artwork colors">
    <div className={styles.content}>
        {failed ? <p className={styles.message} role="alert">Colors couldn’t load. <button type="button" className={styles.retry} onClick={() => { setFailed(false); setAttempt(value => value + 1); }}>Try again</button></p>
          : !sample ? <p className={styles.message} role="status">Finding dominant colors…</p>
          : !palette.length ? <p className={styles.message}>No visible colors found in this image.</p>
          : <ul className={styles.swatches} aria-label="Dominant image colors">{palette.map(color => <li key={color.hex}>
            <button type="button" className={styles.swatch} onClick={event => { selectedButton.current = event.currentTarget; copy(color.hex); }} aria-label={`Copy ${color.hex}, approximately ${Math.round(color.share * 100)}% of sampled image`} title={`Copy ${color.hex}`}>
              <span className={styles.chip} style={{ backgroundColor: color.hex }} />
              <span className={styles.hex}>{color.hex}</span>
            </button>
          </li>)}</ul>}
    </div>
    <div className={styles.feedback}>
      <span className={styles.status} role="status">{copied ? `${copied} copied` : ""}</span>
      {manual && <div className={styles.manual} onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); setManual(""); selectedButton.current?.focus({ preventScroll: true }); } }}>
        <label>Copy HEX value <input ref={input} readOnly value={manual} onFocus={event => event.currentTarget.select()} /></label>
        <button type="button" aria-label="Close color copy" onClick={() => { setManual(""); selectedButton.current?.focus({ preventScroll: true }); }}>×</button>
      </div>}
    </div>
    {sample && palette.length > 0 && palette.length < 8 && <span className="sr-only">Only {palette.length} distinct {palette.length === 1 ? "color" : "colors"} found.</span>}
  </div>;
}
