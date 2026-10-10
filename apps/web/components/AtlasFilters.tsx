"use client";

import { useEffect, useId, useRef, useState, type ReactNode, type RefObject } from "react";
import { useExplorerView } from "./ExplorerFrame";
import { AtlasSearchField } from "./AtlasSearchField";

export function focusAtlasSearch(input: HTMLInputElement | null) {
  if (!input) return;
  const toggle = input.closest(".atlas-filter-system")?.querySelector<HTMLButtonElement>(".atlas-filter-toggle");
  if (toggle?.getClientRects().length && toggle.getAttribute("aria-expanded") === "false") toggle.click();
  requestAnimationFrame(() => {
    input.scrollIntoView({ block: "center" });
    input.focus({ preventScroll: true });
  });
}

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

export function AtlasFilters({ searchRef, query, onQuery, onReset, placeholder, searchLabel, columns, activeCount = 0, initialExpanded = false, actions, resetLabel = "Reset view", children }: {
  searchRef: RefObject<HTMLInputElement | null>; query: string; onQuery: (value: string) => void;
  onReset: () => void; placeholder: string; searchLabel?: string; columns?: number; activeCount?: number; initialExpanded?: boolean; actions?: ReactNode; resetLabel?: string; children: ReactNode;
}) {
  const [expanded, setExpanded] = useState(initialExpanded);
  const view = useExplorerView();
  const fullView = view?.fullView ?? false;
  const filterCount = activeCount + Number(Boolean(query.trim()));
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
      if (event.defaultPrevented || event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey || document.querySelector("dialog[open]")) return;
      const compact = fullView || window.matchMedia("(max-width: 760px)").matches;
      if (compact ? !toggle.current?.getClientRects().length : !searchRef.current?.getClientRects().length) return;
      if (event.target instanceof Element && event.target.closest("input,textarea,select,[contenteditable]")) return;
      event.preventDefault();
      if (compact) setExpanded(true);
      focusFrame = requestAnimationFrame(() => searchRef.current?.focus());
    }
    window.addEventListener("keydown", shortcut);
    return () => { window.removeEventListener("keydown", shortcut); cancelAnimationFrame(focusFrame); };
  }, [searchRef, fullView]);

  const resetButton = <button type="button" className="reset-button" onClick={() => { onReset(); if (fullView || window.matchMedia("(max-width: 760px)").matches) close(); else { setExpanded(false); searchRef.current?.focus(); } }}>{resetLabel}</button>;
  return <div className="atlas-filter-system" data-expanded={expanded} data-view-controls={Boolean(view)} onKeyDown={event => { if (event.key === "Escape" && expanded && toggle.current?.getClientRects().length) { event.preventDefault(); event.stopPropagation(); close(); } }}>
    <AtlasSearchField className="search-field" inputRef={searchRef} label={searchLabel ?? "Search"} placeholder={placeholder} value={query} onChange={onQuery} shortcut />
    {actions ? <div className="atlas-search-actions">{actions}{resetButton}</div> : resetButton}
    <div className="atlas-view-tools">
      <button ref={toggle} type="button" className="atlas-filter-toggle" aria-label="Filters" aria-expanded={expanded} aria-controls={panelID} onClick={() => setExpanded(value => !value)}><span><svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14M7 3v4m6 1v4m-7 1v4" /></svg>Filters{filterCount > 0 && <span className="atlas-filter-count">{filterCount}</span>}</span><span>{expanded ? "Hide" : "Show"}<span aria-hidden="true">{expanded ? "−" : "+"}</span></span></button>
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
  function focusAfterRemoval(button: HTMLButtonElement) {
    if (!window.matchMedia("(max-width: 760px)").matches) { searchRef.current?.focus(); return; }
    // Don't summon the phone keyboard when a visitor is simply removing a chip.
    const group = button.parentElement;
    const toggle = group?.previousElementSibling?.querySelector<HTMLButtonElement>(".atlas-filter-toggle");
    requestAnimationFrame(() => {
      const target = group?.isConnected ? group.querySelector<HTMLButtonElement>("button") : toggle;
      target?.focus({ preventScroll: true });
    });
  }
  return <div className="active-filters" aria-label="Active filters"><span>Filtered by</span>
    {filters.map(filter => <button key={filter.key} type="button" aria-label={`Remove ${filter.label} filter`} onClick={event => { filter.remove(); focusAfterRemoval(event.currentTarget); }}>{filter.label}<span aria-hidden="true">×</span></button>)}
    <button className="clear-filters" type="button" onClick={event => { onClear(); focusAfterRemoval(event.currentTarget); }}>Clear filters</button>
  </div>;
}
