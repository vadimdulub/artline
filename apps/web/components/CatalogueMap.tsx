"use client";
import dynamic from "next/dynamic";
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { apiRequest, errorMessage } from "@/lib/api";
import { connectionYears, mapKindNames, connectionKey, connectionPlaceKey, placeGroups, placeKind, placeRecordCount, placeTopics, relationLabel, sourceHref, type LocatedItem, type MapItem, type MapKind, type MapRecord, type PlaceConnection, type PlaceGroup } from "@/lib/map";
import { MapImage, MapSymbol } from "./MapVisuals";
import { MapRecordJourney } from "./MapRecordJourney";
import { MapShare } from "./MapShare";
import { MapMenu } from "./MapMenu";
import { LoadingIndicator } from "./LoadingIndicator";
import "./CatalogueMap.css";
const MapSurface = dynamic(() => import("./MapSurface"), { ssr: false, loading: () => <div className="map-loading"><LoadingIndicator label="Opening the map…" /></div> });

function PlacePreview({ place }: { place: PlaceGroup }) {
  const work = place.entries.find(e => e.item.image)?.item;
  return <span className={`map-place-preview is-${placeKind(place)}`}>{work?.image ? <MapImage key={work.image} src={work.image} alt="" kind={work.kind} compact /> : <MapSymbol kind={placeKind(place)} />}</span>;
}

export function CatalogueMap({ items, total, loading, error, onRetry, range, onOpen, children, controls, relations, headingId }: {
  items: MapItem[]; total: number; loading: boolean; error?: string; onRetry: () => void;
  range: { start: number; end: number }; onOpen: (item: MapItem) => void; children?: ReactNode; controls?: ReactNode; relations?: string[]; headingId?: string;
}) {
  const params = new URLSearchParams(useQueryString());
  const highlightRegions = params.get("map_regions") !== "off";
  const detail = params.get("map_detail") ?? "all", selected = params.get("map_place") ?? "";
  const panel = params.get("map_panel") ?? "places", recordKey = params.get("map_record") ?? "", stop = params.get("map_stop") ?? "";
  const missing = panel === "missing";
  const hasEvents = items.some(item => item.kind === "event");
  const eventsOnly = hasEvents && items.every(item => item.kind === "event");
  const booksOnly = items.length > 0 && items.every(item => item.kind === "book");
  const artists = items.filter(item => item.kind === "artist");
  const relationKey = relations ? [...relations].sort().join(",") : "all";
  const identities = JSON.stringify(items.map(({ id, kind }) => ({ id, kind })));
  const key = `${range.start}:${range.end}:${relationKey}:${identities}`;
  const [result, setResult] = useState<{ key: string; records: Record<string, MapRecord>; error?: string }>();
  const [retry, setRetry] = useState(0), [find, setFind] = useState("");
  const [hovered, setHovered] = useState("");
  const listHeading = useRef<HTMLHeadingElement>(null), focusSelection = useRef(false), filterID = useId(), findID = useId();
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
  const failure = error ?? (result?.key === key ? result.error : undefined);
  const busy = !failure && (loading || result?.key !== key);
  const records = !busy && !failure ? result?.records : undefined;
  const entries: LocatedItem[] = useMemo(() => items.flatMap(item => (records?.[`${item.kind}:${item.id}`]?.connections ?? []).map(connection => ({ item, connection }))), [items, records]);
  const allGroups = useMemo(() => placeGroups(entries), [entries]);
  const focusedItem = items.find(item => `${item.kind}:${item.id}` === recordKey);
  const focusedRecord = focusedItem && records?.[recordKey];
  const scopedGroups = useMemo(() => focusedRecord ? placeGroups(entries.filter(e => `${e.item.kind}:${e.item.id}` === recordKey)) : allGroups, [focusedRecord, entries, recordKey, allGroups]);
  const groups = useMemo(() => scopedGroups.filter(g => detail === "all" || (detail === "country" ? g.country : !g.country)), [scopedGroups, detail]);
  const showRegions = highlightRegions && groups.some(g => g.entries.some(e => e.item.kind === "event"));
  const mappedRecords = new Set(groups.flatMap(g => g.entries.map(e => `${e.item.kind}:${e.item.id}`)));
  const recordItems = items.filter(item => records?.[`${item.kind}:${item.id}`]?.connections.length);
  const located = new Set(allGroups.flatMap(g => g.entries.map(e => `${e.item.kind}:${e.item.id}`)));
  const unlocated = items.filter(i => !located.has(`${i.kind}:${i.id}`));
  const selectedConnection = focusedRecord?.connections.find(c => connectionKey(c) === stop);
  const selectedPlace = recordKey ? selectedConnection ? connectionPlaceKey(selectedConnection) : "" : selected;
  const group = groups.find(g => g.key === selectedPlace);
  const visible = groups.filter(g => g.name.toLocaleLowerCase().includes(find.trim().toLocaleLowerCase()));
  const selectedKey = group?.key;
  useEffect(() => {
    if (!focusSelection.current || !selectedKey) return;
    focusSelection.current = false;
    listHeading.current?.focus({ preventScroll: true });
    if (window.matchMedia("(max-width: 760px)").matches) listHeading.current?.scrollIntoView({ block: "nearest" });
  }, [selectedKey]);
  function selectConnection(c: PlaceConnection) { setHovered(""); updateQuery({ map_stop: connectionKey(c), map_place: connectionPlaceKey(c) || null, map_detail: null }, true); }
  function selectRecord(item: MapItem) {
    const first = records?.[`${item.kind}:${item.id}`]?.connections[0];
    setHovered(""); setFind("");
    updateQuery({ map_panel: "records", map_record: `${item.kind}:${item.id}`, map_stop: first ? connectionKey(first) : null, map_place: first ? connectionPlaceKey(first) || null : null, map_detail: null }, true);
  }
  function selectPlace(value: string) {
    const connection = focusedRecord?.connections.find(c => connectionPlaceKey(c) === value);
    if (connection) { selectConnection(connection); return; }
    focusSelection.current = true; setHovered(""); updateQuery({ map_place: value, map_panel: null, map_record: null, map_stop: null }, true);
  }
  function switchPanel(value: string) { setFind(""); updateQuery({ map_panel: value === "places" ? null : value, map_record: null, map_stop: null, map_place: null }, true); }
  function clearPlace() { setFind(""); updateQuery({ map_place: null, map_stop: null }, true); }
  const Heading = headingId ? "h1" : "h2";
  const PlaceHeading = headingId ? "h2" : "h3";
  const year = (value: number) => value < 0 ? `${Math.abs(value).toLocaleString("en-GB")} BCE` : String(value);
  const title = artists.length === 1 ? artists[0].title : eventsOnly ? "Events on the map" : booksOnly ? "A world of books" : "Explore places";
  return <section className="catalogue-map" aria-label="Places connected with these results" aria-busy={busy}>
    <div className="map-introduction">
      <div><div className="map-title-line"><Heading id={headingId} tabIndex={headingId ? -1 : undefined}>{title}</Heading>{headingId && <span className="map-year-range" aria-label="Years in view">{year(range.start)}–{year(range.end)}</span>}</div><p role="status">{failure ? "Places are temporarily unavailable" : busy ? "Finding places…" : `${groups.length} ${groups.length === 1 ? "place" : "places"} · ${mappedRecords.size} ${mappedRecords.size === 1 ? "record" : "records"} on the map`}</p></div>
      <div className="map-header-actions"><MapShare /><MapMenu className="map-options" label="Map options"><div className="map-options-panel">
        <label htmlFor={filterID}>Show locations<select id={filterID} disabled={!!focusedRecord} value={detail} onChange={e => updateQuery({ map_detail: e.target.value === "all" ? null : e.target.value, map_place: null, map_stop: null }, true)}><option value="all">All recorded places</option><option value="city">Cities and local areas</option><option value="country">Countries only</option></select></label>
        {hasEvents && <label className="map-region-toggle"><input type="checkbox" checked={highlightRegions} onChange={e => updateQuery({ map_regions: e.target.checked ? null : "off" }, true)} />Highlight event regions</label>}
        <p>Country outlines show modern geography. Shading identifies a recorded event country, not its historical boundaries.</p>
      </div></MapMenu></div>
    </div>
    {controls}
    {focusedItem && focusedRecord && <div className="map-focus-strip"><span>Following <strong>{focusedItem.title}</strong></span><button onClick={() => switchPanel("records")}>Show all records <span aria-hidden="true">×</span></button></div>}
    <div className="map-workspace">
      <div className="map-canvas-wrap"><MapSurface busy={busy || !!failure} highlightRegions={showRegions} groups={groups} selected={group?.key ?? ""} hovered={hovered} onSelect={selectPlace} onReset={clearPlace} />
        {(busy || failure) && <div className="map-updating" aria-hidden="true">{!failure && <LoadingIndicator label="Finding places…" />}</div>}
        {!busy && !failure && <div className="map-canvas-key"><span><i className="map-city-key" />City or area</span><span><i className="map-country-key" />Country</span>{showRegions && <span><i className="map-region-key" />Event region</span>}</div>}
      </div>
      <aside className="map-place-panel" aria-label="Place details">
        {failure ? <div className="map-state" role="alert"><PlaceHeading>Places couldn’t load</PlaceHeading><p>{failure}</p><button onClick={() => { setResult(undefined); setRetry(v => v + 1); onRetry(); }}>Try again</button></div> : busy ? <div className="map-state"><LoadingIndicator label="Finding place evidence…" /></div> : <>
          <div className="map-list-tabs" role="group" aria-label="Map results"><button aria-pressed={panel === "places"} onClick={() => switchPanel("places")}>Places ({focusedRecord ? allGroups.length : groups.length})</button><button aria-pressed={panel === "records"} onClick={() => switchPanel("records")}>Records ({recordItems.length})</button><button aria-pressed={missing} onClick={() => switchPanel("missing")}>Not mapped ({unlocated.length})</button></div>
          {panel === "records" ? focusedItem && focusedRecord ? <MapRecordJourney item={focusedItem} record={focusedRecord} selected={stop} headingLevel={headingId ? 2 : 3} onSelect={selectConnection} onOpen={onOpen} onBack={() => switchPanel("records")} /> : <>
            <PlaceHeading>Follow a record</PlaceHeading><p className="map-panel-intro">Explore its documented places in date order.</p>
            {recordKey && <p className="map-panel-intro" role="status">This record is not on the current page. Choose another record below.</p>}
            <div className="map-record-list">{recordItems.map(item => <button className="map-record-card" key={`${item.kind}:${item.id}`} onClick={() => selectRecord(item)}><span className="map-place-preview">{item.image ? <MapImage key={item.image} src={item.image} alt="" kind={item.kind} compact /> : <MapSymbol kind={item.kind} />}</span><span><small>{mapKindNames[item.kind]}</small><strong>{item.title}</strong><small>{records?.[`${item.kind}:${item.id}`]?.connections.length} connections</small></span></button>)}</div>
            {!recordItems.length && <p className="map-panel-intro">No place connections for this selection. Try other years or place types, or open a record from Not mapped.</p>}
          </> : missing ? <><PlaceHeading ref={listHeading} tabIndex={-1}>Places still to discover</PlaceHeading><p className="map-panel-intro">No mapped connection for these place types and years. You can still explore each record.</p><ul className="map-unlocated">{unlocated.map(item => <li key={`${item.kind}:${item.id}`}><button onClick={() => onOpen(item)}>{item.title}</button>{records?.[`${item.kind}:${item.id}`]?.connections.map((c, index) => <small key={index}>{c.place} · {relationLabel(c.relation)} · coordinates unresolved</small>)}</li>)}</ul></> : group ? <>
            <button className="map-back" onClick={clearPlace}>← All places</button>
            <div className="map-place-heading"><PlaceHeading ref={listHeading} tabIndex={-1}>{group.name}</PlaceHeading><p>{group.country ? "Country-level location" : group.precision === "recorded point" ? "Recorded location · precision unverified" : "Approximate city / area"} · {placeRecordCount(group)} {placeRecordCount(group) === 1 ? "record" : "records"}</p></div>
            <div className="map-place-records">{[...group.entries].sort((a,b) => (a.connection.start ?? Infinity) - (b.connection.start ?? Infinity)).map(({ item, connection: c }, index) => <article className={`map-connection is-${item.kind}`} key={`${item.kind}:${item.id}:${index}`}>
              {item.image && <button className="map-record-image" aria-label={`Open ${item.title}`} onClick={() => onOpen(item)}><MapImage key={item.image} src={item.image} alt={item.title} kind={item.kind} /></button>}
              <div className="map-connection-body"><span className="map-record-kind"><MapSymbol kind={item.kind} />{mapKindNames[item.kind]}</span><button className="map-record-title" onClick={() => onOpen(item)}>{item.title}</button>{item.context && item.context !== "Unclassified" && <p>{item.context}</p>}{item.years && item.years !== connectionYears(c) && <time className="map-record-years">{item.years}</time>}<div className="map-place-fact"><span>{relationLabel(c.relation)}</span><time>{connectionYears(c).replace("Association dates unrecorded", "Location dates not recorded")}</time></div><button className="map-follow-record" onClick={() => selectRecord(item)}>Follow places</button><details><summary>Source & location</summary><p>{c.note}</p>{sourceHref(c.sourceUrl) ? <a href={sourceHref(c.sourceUrl)} target="_blank" rel="noreferrer">{c.sourceLabel}</a> : <p>{c.sourceLabel}</p>}</details></div>
            </article>)}</div>
          </> : <>
            <PlaceHeading ref={listHeading} tabIndex={-1}>Discover a place</PlaceHeading>
            {groups.length > 0 && <div className="map-place-search"><label className="sr-only" htmlFor={findID}>Find a mapped place on this page</label><input id={findID} type="search" placeholder="Find a mapped place" value={find} onChange={e => setFind(e.target.value)} />{find && <button aria-label="Clear place search" onClick={() => setFind("")}>×</button>}</div>}
            {visible.length ? <div className="map-place-list">{visible.map(place => <button className="map-place-card" key={place.key} onClick={() => selectPlace(place.key)} onMouseEnter={() => setHovered(place.key)} onMouseLeave={() => setHovered("")} onFocus={() => setHovered(place.key)} onBlur={() => setHovered("")}><PlacePreview place={place} /><span><strong>{place.name}</strong><small>{placeTopics(place)}</small><small>{placeRecordCount(place)} {placeRecordCount(place) === 1 ? "record" : "records"}{place.country ? " · country" : ""}</small></span><span className="map-place-chevron" aria-hidden="true">›</span></button>)}</div> : <div className="map-empty"><p>{relationKey === "" ? "Choose at least one place type above to explore an artist’s life or paintings." : find ? `No mapped place matches “${find}” on this page.` : items.length ? "No mapped places for this selection. Try all recorded places, or explore the records in Not mapped." : total ? "Narrow the painter filters or choose Top 100 painters to load individual records for the map." : "No records match these filters. Choose other years or remove a filter."}</p>{find && <button onClick={() => setFind("")}>Show every place</button>}{detail !== "all" && <button onClick={() => updateQuery({ map_detail: null }, true)}>Show all location types</button>}</div>}
          </>}
        </>}
      </aside>
    </div>
    <div className="map-bottom-bar"><p className="map-coverage">{failure ? "Place evidence unavailable" : busy ? "Finding documented places…" : `${located.size} of ${items.length} loaded records located · ${total.toLocaleString("en-GB")} matching records`}</p><details className="map-guide"><summary>About this map</summary><div><p>Only the current page of results is mapped. Choose a place to see its works, people or events. Nearby places group together as you zoom out.</p><p>City and area markers are approximate. Country markers identify a whole country; they are not an exact site. Modern outlines provide orientation, not historical boundaries. Country affiliations do not establish where a work was created.</p><p>The year controls select catalogue records and their dated place connections. Unknown association dates remain unknown. Follow a record to browse its sourced connections in date order; this does not establish a complete travel route.</p>{Object.values(records ?? {}).some(r => r.truncated) && <p>Some records have additional connections. Up to 32 matching connections per record are shown.</p>}</div></details></div>
    {children}
  </section>;
}
