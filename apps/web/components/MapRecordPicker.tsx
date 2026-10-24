"use client";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import type { MapItem, MapRecord } from "@/lib/map";
import { AtlasSearchField } from "./AtlasSearchField";
import { MapPickerFrame, isMapPickerControl } from "./MapPickerFrame";
import { MapImage } from "./MapVisuals";

const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
const key = (item: MapItem) => `${item.kind}:${item.id}`;
export function MapRecordPicker({ name, items, records, active, selected, enabled, located, onVisibility, onInspect, onPreview, colorStyle }: {
  name: string; items: MapItem[]; records: Record<string, MapRecord>; active: boolean; selected: string;
  enabled: (item: MapItem) => boolean; located: Set<string>; onVisibility: (item: MapItem, checked: boolean) => void;
  onInspect: (item: MapItem, query: string) => void; onPreview: (record: string) => void; colorStyle: (item: MapItem) => CSSProperties;
}) {
  const details = useRef<HTMLDetailsElement>(null);
  const [search, setSearch] = useState(""), [open, setOpen] = useState(false);
  const mapped = items.filter(item => located.has(key(item)));
  const count = mapped.filter(enabled).length, query = normalize(search.trim());
  const matches = (query ? items : mapped).filter(item => normalize([item.title, item.context ?? "", item.years ?? "", ...(records[key(item)]?.connections.map(connection => connection.place) ?? [])].join(" ")).includes(query)).sort((a, b) => a.title.localeCompare(b.title));
  function close() { if (details.current) { details.current.open = false; details.current.querySelector("summary")?.focus(); } }
  useEffect(() => {
    function outside(event: MouseEvent) { if (event.target instanceof Node && details.current && !event.composedPath().includes(details.current) && !isMapPickerControl(event.target)) details.current.open = false; }
    document.addEventListener("click", outside);
    return () => document.removeEventListener("click", outside);
  }, []);
  return <MapPickerFrame name={name} className="map-record-picker"><details ref={details} className="multi-filter" onToggle={event => setOpen(event.currentTarget.open)} onKeyDown={event => {
    if (event.key === "Escape" && event.currentTarget.open) { event.preventDefault(); event.stopPropagation(); close(); }
  }}>
    <summary aria-label={`${name}: ${!active ? "Hidden" : `${count} selected`}`}><span>{name}</span><strong>{!active ? "Hidden" : `${count} shown`}</strong><svg aria-hidden="true" className="filter-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="m5 7.5 5 5 5-5" /></svg></summary>
    <div className="multi-filter-panel" hidden={!open}>
      <AtlasSearchField label={`Search ${name.toLowerCase()}`} placeholder={`Find ${name.toLowerCase()}…`} value={search} onChange={setSearch} />
      <div className="map-picker-records">{matches.map(item => <div className={`map-selection-row${key(item) === selected ? " is-selected" : ""}`} style={colorStyle(item)} key={key(item)} onMouseEnter={() => onPreview(key(item))} onMouseLeave={() => onPreview("")} onFocusCapture={() => onPreview(key(item))} onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) onPreview(""); }}>
        <label className="map-record-check"><input type="checkbox" aria-label={`Show ${item.title}`} checked={enabled(item)} disabled={!active} onChange={event => onVisibility(item, event.target.checked)} /></label>
        <button className={`map-selection-name${item.image ? " has-image" : ""}`} aria-current={key(item) === selected ? "true" : undefined} onClick={() => onInspect(item, query)}>
          {item.image && <span className="map-index-image" aria-hidden="true"><MapImage key={item.image} src={item.image} alt="" kind={item.kind} compact /></span>}
          <span className="map-selection-copy"><strong><i className="map-picker-record-dot" aria-hidden="true" />{item.title}</strong><small>{[item.kind === "artwork" || item.kind === "book" ? item.context : undefined, item.years, !located.has(key(item)) ? "No map location" : undefined].filter(Boolean).join(" · ")}</small></span>
        </button>
      </div>)}</div>
      {!matches.length && <p role="status">{query ? `No records or places match “${search}” on this page.` : `No mapped ${name.toLowerCase()} in this selection.`}</p>}
    </div>
  </details></MapPickerFrame>;
}
