"use client";

import { useEffect, useId, useRef, useState } from "react";

export function SelectionHint({ label, children }: { label: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const button = useRef<HTMLButtonElement>(null);
  const hint = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const dismiss = (event: KeyboardEvent) => {
      if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); setOpen(false); }
    };
    const dismissOutside = (event: PointerEvent) => {
      if (!hint.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", dismiss, true);
    document.addEventListener("pointerdown", dismissOutside);
    return () => {
      document.removeEventListener("keydown", dismiss, true);
      document.removeEventListener("pointerdown", dismissOutside);
    };
  }, [open]);

  return <span ref={hint} className="selection-hint"
    onPointerEnter={event => { if (event.pointerType === "mouse") setOpen(true); }}
    onPointerLeave={() => { if (document.activeElement !== button.current) setOpen(false); }}>
    <button ref={button} type="button" className="selection-info" aria-label={label} aria-describedby={id}
      onFocus={() => setOpen(true)} onBlur={() => setOpen(false)} onClick={() => setOpen(true)}>
      <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true"><circle cx="10" cy="10" r="7.5" /><path d="M10 9v5" /><circle cx="10" cy="6" r=".8" fill="currentColor" stroke="none" /></svg>
    </button>
    <span id={id} role="tooltip" className="selection-tip" hidden={!open}>{children}</span>
  </span>;
}
