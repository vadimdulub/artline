"use client";

import { useEffect, useId, useRef, useState, type ReactNode, type RefObject } from "react";
import { useExplorerView } from "./ExplorerFrame";

export function AtlasSelect({ label, value, onChange, options }: {
  label: string; value: string; onChange: (value: string) => void; options: { value: string; label: string }[];
}) {
  return <label className="atlas-select"><span>{label}</span><select aria-label={label} value={value} onChange={event => onChange(event.target.value)}>{options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>;
}

export function AtlasCheckbox({ label, checked, onChange, children }: {
  label: string; checked: boolean; onChange: (checked: boolean) => void; children?: ReactNode;
}) {
  return <div className="popular-filter-control"><label className="popular-filter"><input type="checkbox" checked={checked} onChange={event => onChange(event.target.checked)} /><span>{label}</span></label>{children}</div>;
}

export function AtlasFilters({ searchRef, query, onQuery, onReset, placeholder, searchLabel, columns, activeCount = 0, actions, resetLabel = "Reset view", children }: {
  searchRef: RefObject<HTMLInputElement | null>; query: string; onQuery: (value: string) => void;
  onReset: () => void; placeholder: string; searchLabel?: string; columns?: number; activeCount?: number; actions?: ReactNode; resetLabel?: string; children: ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const view = useExplorerView();
  const fullView = view?.fullView ?? false;
  const panelID = useId();
  const toggle = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  function close() { setExpanded(false); toggle.current?.focus(); }
  useEffect(() => {
    const mobile = window.matchMedia("(max-width: 760px)");
    const resize = () => { if (mobile.matches && panel.current?.contains(document.activeElement)) setExpanded(true); };
    mobile.addEventListener("change", resize);
    return () => mobile.removeEventListener("change", resize);
  }, []);
  useEffect(() => {
    let focusFrame = 0;
    function shortcut(event: KeyboardEvent) {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || document.querySelector("dialog[open]")) return;
      if (event.target instanceof Element && event.target.closest("input,textarea,select,[contenteditable]")) return;
      event.preventDefault();
      if (fullView) setExpanded(true);
      focusFrame = requestAnimationFrame(() => searchRef.current?.focus());
    }
    window.addEventListener("keydown", shortcut);
    return () => { window.removeEventListener("keydown", shortcut); cancelAnimationFrame(focusFrame); };
  }, [searchRef, fullView]);

  const resetButton = <button className="reset-button" onClick={() => { onReset(); if (fullView) close(); else { setExpanded(false); searchRef.current?.focus(); } }}>{resetLabel}</button>;
  return <div className="atlas-filter-system" data-expanded={expanded} data-view-controls={Boolean(view)} onKeyDown={event => { if (event.key === "Escape" && expanded && toggle.current?.getClientRects().length) { event.preventDefault(); event.stopPropagation(); close(); } }}>
    <label className="search-field"><span>Search</span><input ref={searchRef} aria-label={searchLabel} aria-keyshortcuts="/" type="search" maxLength={200} placeholder={placeholder} value={query} onChange={event => onQuery(event.target.value)} /><kbd aria-hidden="true">/</kbd></label>
    {actions ? <div className="atlas-search-actions">{actions}{resetButton}</div> : resetButton}
    <div className="atlas-view-tools">
      <button ref={toggle} type="button" className="atlas-filter-toggle" aria-label="Filters" aria-expanded={expanded} aria-controls={panelID} onClick={() => setExpanded(value => !value)}><span>Filters{activeCount > 0 && <span className="atlas-filter-count">{activeCount}</span>}</span><span>{expanded ? "Hide" : "Show"}<span aria-hidden="true">{expanded ? "−" : "+"}</span></span></button>
      {view && <button type="button" className="atlas-full-view" aria-pressed={fullView} title={fullView ? "Restore the header and filters (Esc)" : "Hide the header and filters for more space"} onClick={() => { setExpanded(false); view.setFullView(!fullView); }}>
        <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d={fullView ? "M3 7h4V3m6 0v4h4M3 13h4v4m6 0v-4h4" : "M7 3H3v4m10-4h4v4M3 13v4h4m6 0h4v-4"}/></svg>
        {fullView ? "Exit full view" : "Full view"}
      </button>}
    </div>
    <div ref={panel} id={panelID} className="atlas-filter-row" data-expanded={expanded} style={columns ? { ["--atlas-filter-columns" as string]: columns } : undefined}>{children}<button type="button" className="atlas-filter-close" onClick={close}>Close filters</button></div>
  </div>;
}

export function ActiveFilters({ filters, onClear, searchRef }: {
  filters: { key: string; label: string; remove: () => void }[];
  onClear: () => void; searchRef: RefObject<HTMLInputElement | null>;
}) {
  if (!filters.length) return null;
  return <div className="active-filters" aria-label="Active filters"><span>Filtered by</span>
    {filters.map(filter => <button key={filter.key} type="button" aria-label={`Remove ${filter.label} filter`} onClick={() => { filter.remove(); searchRef.current?.focus(); }}>{filter.label}<span aria-hidden="true">×</span></button>)}
    <button className="clear-filters" type="button" onClick={() => { onClear(); searchRef.current?.focus(); }}>Clear filters</button>
  </div>;
}
