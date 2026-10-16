"use client";
import dynamic from "next/dynamic";
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { apiRequest, errorMessage } from "@/lib/api";
import { connectionYears, placeGroups, sourceHref, type LocatedItem, type MapItem, type MapKind, type MapRecord } from "@/lib/map";
import { LoadingIndicator } from "./LoadingIndicator";
import "./CatalogueMap.css";
const MapSurface = dynamic(() => import("./MapSurface"), { ssr: false, loading: () => <div className="map-loading"><LoadingIndicator label="Opening the map…" /></div> });

export function CatalogueMap({ items, total, loading, error, onRetry, range, onOpen, children, controls, relations }: {
  items: MapItem[]; total: number; loading: boolean; error?: string; onRetry: () => void;
  range: { start: number; end: number }; onOpen: (item: MapItem) => void; children?: ReactNode; controls?: ReactNode; relations?: string[];
}) {
  const params = new URLSearchParams(useQueryString());
  const highlightRegions = params.get("map_regions") !== "off";
  const hasEvents = items.some(item => item.kind === "event");
  const eventsOnly = hasEvents && items.every(item => item.kind === "event");
  const relationKey = relations ? [...relations].sort().join(",") : "all";
  const identities = JSON.stringify(items.map(({ id, kind }) => ({ id, kind })));
  const key = `${range.start}:${range.end}:${relationKey}:${identities}`;
  const [result, setResult] = useState<{ key: string; records: Record<string, MapRecord>; error?: string }>();
  const [retry, setRetry] = useState(0), [selected, setSelected] = useState(""), [detail, setDetail] = useState("all"), [missing, setMissing] = useState(false);
  const listHeading = useRef<HTMLHeadingElement>(null), filterID = useId();
  useEffect(() => {
    if (loading || error) return;
    const controller = new AbortController();
    async function load() {
      const ids = JSON.parse(identities) as Pick<MapItem, "id" | "kind">[];
      const records: Record<string, MapRecord> = {};
      // Serial chunks bound both URL size and pressure on the catalogue pool.
      for (const kind of ["artist", "artwork", "book", "event"] as MapKind[]) {
        if (relationKey === "") continue;
        const selected = [...new Set(ids.filter(i => i.kind === kind).map(i => i.id))];
        for (let offset = 0; offset < selected.length; offset += 80) {
          const query = new URLSearchParams({ kind, start: String(range.start), end: String(range.end) });
          if (relationKey !== "all" && (kind === "artist" || kind === "artwork")) relationKey.split(",").forEach(value => query.append("relation", value));
          selected.slice(offset, offset + 80).forEach(id => query.append("id", id));
          const data = await apiRequest<{ records: MapRecord[] }>(`map/locations?${query}`, { signal: controller.signal });
          data.records.forEach(record => { records[`${kind}:${record.id}`] = record; });
        }
      }
      if (!controller.signal.aborted) setResult({ key, records });
    }
    load().catch(e => { if (!controller.signal.aborted) setResult({ key, records: {}, error: errorMessage(e) }); });
    return () => controller.abort();
  }, [identities, relationKey, key, range.start, range.end, retry, loading, error]);
  const busy = loading || result?.key !== key;
  const failure = error ?? (result?.key === key ? result.error : undefined);
  const records = !busy && !failure ? result?.records : undefined;
  const entries: LocatedItem[] = useMemo(() => items.flatMap(item => (records?.[`${item.kind}:${item.id}`]?.connections ?? []).map(connection => ({ item, connection }))), [items, records]);
  const allGroups = useMemo(() => placeGroups(entries), [entries]);
  const groups = useMemo(() => allGroups.filter(g => detail === "all" || (detail === "country" ? g.country : !g.country)), [allGroups, detail]);
  const located = new Set(allGroups.flatMap(g => g.entries.map(e => `${e.item.kind}:${e.item.id}`)));
  const unlocated = items.filter(i => !located.has(`${i.kind}:${i.id}`));
  const group = groups.find(g => g.key === selected);
  const visible = group ? [group] : groups;
  function selectPlace(key: string) { setSelected(key); setMissing(false); requestAnimationFrame(() => listHeading.current?.focus()); }
  return <section className="catalogue-map" aria-label="Places connected with these results" aria-busy={busy}>
    <div className="map-introduction"><div><h2>{eventsOnly ? "Where history happened" : "Places behind the collection"}</h2><p>{eventsOnly ? "Explore the places and regions connected with events." : "Explore where works were made and lives unfolded."}</p></div><label htmlFor={filterID}>Place detail<select id={filterID} value={detail} onChange={e => { setDetail(e.target.value); setSelected(""); setMissing(false); }}><option value="all">All recorded places</option><option value="city">Local places</option><option value="country">Countries only</option></select></label></div>
    {controls}
    {hasEvents && <div className="map-region-control"><label><input type="checkbox" checked={highlightRegions} onChange={e => updateQuery({ map_regions: e.target.checked ? null : "off" }, true)} />Highlight event regions</label><p>Shaded areas are recorded event countries, shown with modern outlines. Local events keep their place markers.</p></div>}
    <p className="map-coverage" role="status">{failure ? "Place evidence unavailable" : busy ? "Finding documented places…" : `${located.size} of ${items.length} loaded records located · ${total.toLocaleString("en-GB")} matching records`}</p>
    {failure ? <div className="state-panel" role="alert"><h2>We couldn’t load these places</h2><p>{failure}</p><button onClick={() => { setResult(undefined); setRetry(v => v + 1); onRetry(); }}>Try again</button></div> : busy ? <div className="map-loading"><LoadingIndicator label="Finding place evidence…" /></div> : <>
      <div className="map-workspace"><MapSurface highlightRegions={hasEvents && highlightRegions} groups={groups} selected={group?.key ?? ""} onSelect={selectPlace} />
        <aside className="map-place-panel" aria-label="Place details">
          <div className="map-list-tabs" role="group" aria-label="Map results"><button aria-pressed={!missing} onClick={() => setMissing(false)}>Places ({groups.length})</button><button aria-pressed={missing} onClick={() => setMissing(true)}>Unlocated ({unlocated.length})</button></div>
          <h3 ref={listHeading} tabIndex={-1}>{missing ? "Places still to establish" : group ? group.name : "Explore a place"}</h3>
          {group && !missing && <button className="map-back" onClick={() => setSelected("")}>Show all places</button>}
          {missing ? <><p>These records have no mapped connection for the selected place types and years. Open a record to inspect its evidence.</p><ul className="map-unlocated">{unlocated.map(item => <li key={`${item.kind}:${item.id}`}><button onClick={() => onOpen(item)}>{item.title}</button>{records?.[`${item.kind}:${item.id}`]?.connections.map((c, index) => <small key={index}>{c.place} · {c.relation} · coordinates unresolved</small>)}</li>)}</ul></> : visible.length ? <div className="map-place-list">{visible.map(place => <section className="map-place" key={place.key}>
            {!group && <button className="map-place-title" onClick={() => selectPlace(place.key)}>{place.name}<span>{place.entries.length} connections</span></button>}
            <p className="map-precision">{place.country ? "Country only · marker is a label position" : place.precision === "recorded point" ? "Recorded coordinate · precision unverified" : "Approximate city / area position"}</p>
            {(group ? place.entries : place.entries.slice(0, 2)).map(({ item, connection: c }, index) => <article className="map-connection" key={`${item.kind}:${item.id}:${index}`}>
              {item.image && <img src={item.image} alt="" loading="lazy" />}
              <div><span className="map-relation">{c.relation}</span><button className="map-record-title" onClick={() => onOpen(item)}>{item.title}</button>{item.context && item.context !== "Unclassified" && <p>{item.context}</p>}<time>{connectionYears(c)}</time><details><summary>Place evidence</summary><p>{c.note}</p>{sourceHref(c.sourceUrl) ? <a href={sourceHref(c.sourceUrl)} target="_blank" rel="noreferrer">{c.sourceLabel}</a> : <p>{c.sourceLabel}</p>}</details></div>
            </article>)}
            {!group && place.entries.length > 2 && <button className="map-back" onClick={() => selectPlace(place.key)}>View all {place.entries.length} connections</button>}
          </section>)}</div> : <p>{relationKey === "" ? "Choose at least one place type above to explore an artist’s life or paintings." : items.length ? "No mapped places at this detail level. Try all recorded places, or inspect the unlocated records." : total ? "Narrow the painter filters or choose Top 100 painters to load individual records for the map." : "No records match these filters. Choose other years or remove a filter."}</p>}
        </aside>
      </div>
      <div className="map-footnote"><span><i className="map-city-key" /> City or area</span><span><i className="map-country-key" /> Country only</span>{hasEvents && highlightRegions && <span><i className="map-region-key" /> Event country · modern outline</span>}<p>Modern geography for orientation. Countries of origin and cultural affiliations do not establish where a work was created. Only the loaded page is mapped. Years select records and their dated place connections.</p></div>
      {Object.values(records ?? {}).some(r => r.truncated) && <p className="map-coverage">Some records have more place connections. This view shows up to 32 per record.</p>}
      {children}
    </>}
  </section>;
}
