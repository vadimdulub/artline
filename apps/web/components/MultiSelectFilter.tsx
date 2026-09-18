"use client";
import { useEffect, useId, useRef, useState } from "react";

export type FilterOption = { slug: string; name: string };

export function MultiSelectFilter({ label, allLabel, options, values, onChange, unavailable = false, helpText = "Match any selected value. Different filters combine.", remote, retry }: {
  label: string; allLabel: string; options: FilterOption[]; values: string[];
  onChange: (values: string[]) => void; unavailable?: boolean; helpText?: string;
  remote?: { search: string; onSearch: (value: string) => void; loading: boolean; hasMore: boolean }; retry?: () => void;
}) {
  const details = useRef<HTMLDetailsElement>(null);
  const pointerFocus = useRef(false);
  const helpID = useId();
  const [localSearch, setLocalSearch] = useState("");
  const search = remote?.search ?? localSearch;
  const available = new Set(options.map(option => option.slug));
  const choices = [...options, ...values.filter(value => !available.has(value)).map(value => ({ slug: value, name: value.replaceAll("-", " ") }))];
  const visible = choices.filter(option => remote || values.includes(option.slug) || option.name.toLocaleLowerCase().includes(search.toLocaleLowerCase()));
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
  return <details ref={details} className="multi-filter" onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(); } }} onBlur={event => { if (!pointerFocus.current && event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) event.currentTarget.open = false; }}>
    <summary aria-label={`${label}: ${description}`}><span>{label}</span><strong>{description}</strong><span aria-hidden="true" className="filter-chevron">⌄</span></summary>
    <div className="multi-filter-panel">
      <fieldset aria-describedby={helpID}><legend>{label}</legend><p id={helpID}>{helpText}</p>
        <label className="filter-search"><span className="sr-only">Search {label.toLowerCase()}</span><input type="search" placeholder={`Find ${label.toLowerCase()}…`} maxLength={200} value={search} onChange={event => remote ? remote.onSearch(event.target.value) : setLocalSearch(event.target.value)} /></label>
        <p className="filter-search-status" role="status">{remote?.loading ? "Searching…" : remote?.hasMore ? "Showing 30 matches. Type a name to narrow the list." : `${visible.length} choices${values.length ? ` · ${values.length} selected` : ""}`}</p>
        <div className="filter-checkboxes">{visible.map(option => <label key={option.slug}><input type="checkbox" checked={values.includes(option.slug)} disabled={values.length >= 32 && !values.includes(option.slug)} onChange={() => {
          onChange(values.includes(option.slug) ? values.filter(value => value !== option.slug) : [...values, option.slug]);
          // A bookmarked region absent from the facets disappears on removal.
          // Return focus before its checkbox is unmounted.
          if (!available.has(option.slug)) close();
        }} /><span>{option.name}</span></label>)}</div>
        {unavailable && <p role="alert">Filter choices couldn’t load. {retry && <button type="button" onClick={retry}>Retry choices</button>}</p>}
        {!unavailable && !remote?.loading && visible.length === 0 && <p>No matches. Try another spelling or clear the search.</p>}
        {values.length >= 32 && <p>Up to 32 selections per filter. Remove one to add another.</p>}
      </fieldset>
      <div className="multi-filter-actions"><button type="button" disabled={!values.length} onClick={() => onChange([])}>Clear {label.toLowerCase()}</button><button type="button" onClick={close}>Done</button></div>
    </div>
  </details>;
}
