"use client";
import { useEffect, useId, useRef, useState } from "react";

export type FilterOption = { slug: string; name: string; group?: string; detail?: string; description?: string; searchText?: string };

export function MultiSelectFilter({ label, allLabel, options, values, onChange, single = false, unavailable = false, helpText = "Match any selected value. Different filters combine.", remote, retry }: {
  label: string; allLabel: string; options: FilterOption[]; values: string[];
  onChange: (values: string[]) => void; single?: boolean; unavailable?: boolean; helpText?: string;
  remote?: { search: string; onSearch: (value: string) => void; loading: boolean; hasMore: boolean }; retry?: () => void;
}) {
  const details = useRef<HTMLDetailsElement>(null);
  const pointerFocus = useRef(false);
  const helpID = useId();
  const [localSearch, setLocalSearch] = useState("");
  const search = remote?.search ?? localSearch;
  const available = new Set(options.map(option => option.slug));
  const choices: FilterOption[] = [...options, ...values.filter(value => !available.has(value)).map(value => ({ slug: value, name: value.replaceAll("-", " ") }))];
  const visible = choices.filter(option => remote || values.includes(option.slug) || [option.name, option.group, option.detail, option.description, option.searchText].filter(Boolean).join(" ").toLocaleLowerCase().includes(search.trim().toLocaleLowerCase()));
  const groups = [...new Set(visible.map(option => option.group ?? ""))];
  const description = values.length === 0 ? allLabel : values.length === 1 ? choices.find(option => option.slug === values[0])?.name ?? values[0] : `${values.length} selected`;
  function close() { if (details.current) { details.current.open = false; details.current.querySelector("summary")?.focus(); } }
  useEffect(() => {
    function pointerDown() { pointerFocus.current = true; }
    function keyboard() { pointerFocus.current = false; }
    function outside(event: MouseEvent) {
      pointerFocus.current = false;
      if (event.target instanceof Node && details.current && !details.current.contains(event.target)) details.current.open = false;
    }
    // Inline panels change document flow. Finish the click before collapsing
    // them, so a neighbouring filter cannot move away between down and up.
    document.addEventListener("pointerdown", pointerDown, true);
    document.addEventListener("keydown", keyboard, true);
    document.addEventListener("click", outside);
    return () => {
      document.removeEventListener("pointerdown", pointerDown, true);
      document.removeEventListener("keydown", keyboard, true);
      document.removeEventListener("click", outside);
    };
  }, []);
  return <details ref={details} className="multi-filter" onKeyDown={event => { if (event.key === "Escape" && event.currentTarget.open) { event.preventDefault(); event.stopPropagation(); close(); } }} onBlur={event => { if (!pointerFocus.current && event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false; }}>
    <summary aria-label={`${label}: ${description}`}><span>{label}</span><strong>{description}</strong><span aria-hidden="true" className="filter-chevron">⌄</span></summary>
    <div className="multi-filter-panel">
      <fieldset aria-describedby={helpID}><legend>{label}</legend><p id={helpID}>{helpText}</p>
        <label className="filter-search"><span className="sr-only">Search {label.toLowerCase()}</span><input type="search" placeholder={`Find ${label.toLowerCase()}…`} maxLength={200} value={search} onChange={event => remote ? remote.onSearch(event.target.value) : setLocalSearch(event.target.value)} /></label>
        <p className="filter-search-status" role="status">{remote?.loading ? "Searching…" : remote?.hasMore ? "Showing 30 matches. Type a name to narrow the list." : `${visible.length} choices${values.length ? ` · ${values.length} selected` : ""}`}</p>
        <div className="filter-checkboxes">{groups.map(group => <div key={group} className="filter-option-group" role={group ? "group" : undefined} aria-label={group || undefined}>{group && <h3>{group}</h3>}{visible.filter(option => (option.group ?? "") === group).map(option => <label key={option.slug}><input type={single ? "radio" : "checkbox"} name={single ? helpID : undefined} aria-label={option.name} aria-describedby={option.description || option.detail ? `${helpID}-${option.slug}` : undefined} checked={values.includes(option.slug)} disabled={!single && values.length >= 32 && !values.includes(option.slug)} onChange={() => {
          onChange(single ? [option.slug] : values.includes(option.slug) ? values.filter(value => value !== option.slug) : [...values, option.slug]);
          // A bookmarked region absent from the facets disappears on removal.
          // Return focus before its checkbox is unmounted.
          if (!available.has(option.slug)) close();
        }} /><span className="filter-option-copy"><span>{option.name}</span>{(option.detail || option.description) && <span id={`${helpID}-${option.slug}`} className="filter-option-detail">{option.detail && <span>{option.detail}</span>}{option.description && <span>{option.description}</span>}</span>}</span></label>)}</div>)}</div>
        {unavailable && <p role="alert">Filter choices couldn’t load. {retry && <button type="button" onClick={retry}>Retry choices</button>}</p>}
        {!unavailable && !remote?.loading && visible.length === 0 && <p>No matches. Try another spelling or clear the search.</p>}
        {values.length >= 32 && <p>Up to 32 selections per filter. Remove one to add another.</p>}
      </fieldset>
      <div className="multi-filter-actions"><button type="button" disabled={!values.length} onClick={() => onChange([])}>Clear {label.toLowerCase()}</button><button type="button" onClick={close}>Done</button></div>
    </div>
  </details>;
}
