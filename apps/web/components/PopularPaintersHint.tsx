"use client";

import { useEffect, useId, useRef, useState } from "react";

export function PopularPaintersHint() {
  const [open, setOpen] = useState(false);
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);
  const hint = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const dismissOutside = (event: PointerEvent) => {
      if (!hint.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", dismiss);
    document.addEventListener("pointerdown", dismissOutside);
    return () => {
      document.removeEventListener("keydown", dismiss);
      document.removeEventListener("pointerdown", dismissOutside);
    };
  }, [open]);

  return <span ref={hint} className="selection-hint"
    onPointerEnter={event => { if (event.pointerType === "mouse") setOpen(true); }}
    onPointerLeave={() => { if (document.activeElement !== button.current) setOpen(false); }}>
    <button ref={button} type="button" className="selection-info" aria-label="About the popular painter selection" aria-describedby={id}
      onFocus={() => setOpen(true)} onBlur={() => setOpen(false)} onClick={() => setOpen(true)}>
      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><circle cx="10" cy="10" r="7.5" /><path d="M10 9v5" /><circle cx="10" cy="6" r=".8" fill="currentColor" stroke="none" /></svg>
    </button>
    <span id={id} role="tooltip" className="selection-tip" hidden={!open}>A starting selection of 100 painters based on Pantheon 2025, with editorial corrections. Popularity is a discovery aid, not a measure of artistic quality. Uncheck to explore all painters.</span>
  </span>;
}
