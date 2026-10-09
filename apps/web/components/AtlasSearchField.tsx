"use client";

import { useId, useRef, type RefObject } from "react";

export function AtlasSearchField({ label, placeholder, value, onChange, inputRef, shortcut = false, className = "" }: {
  label: string; placeholder: string; value: string; onChange: (value: string) => void;
  inputRef?: RefObject<HTMLInputElement | null>; shortcut?: boolean; className?: string;
}) {
  const id = useId();
  const localRef = useRef<HTMLInputElement>(null);
  const ref = inputRef ?? localRef;
  return <div className={`atlas-search ${className}`}>
    <label className="sr-only" htmlFor={id}>{label}</label>
    <svg className="search-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5" /><path d="m12.5 12.5 4 4" /></svg>
    <input id={id} ref={ref} type="search" aria-keyshortcuts={shortcut ? "/" : undefined} maxLength={200} placeholder={placeholder} value={value} onChange={event => onChange(event.target.value)} />
    {value && <button type="button" className="search-clear" aria-label={`Clear ${label.toLowerCase()}`} onClick={() => { onChange(""); ref.current?.focus(); }}><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="m6 6 8 8M14 6l-8 8" /></svg></button>}
    {shortcut && <kbd aria-hidden="true">/</kbd>}
  </div>;
}
