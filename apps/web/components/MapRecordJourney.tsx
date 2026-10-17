"use client";
import { useEffect, useRef } from "react";
import { connectionKey, connectionPlaceKey, connectionYears, mapKindNames, relationLabel, sourceHref, type MapItem, type MapRecord, type PlaceConnection } from "@/lib/map";
import { MapImage, MapSymbol } from "./MapVisuals";

export function MapRecordJourney({ item, record, selected, headingLevel, onSelect, onOpen, onBack }: {
  item: MapItem; record: MapRecord; selected: string; headingLevel: 2 | 3;
  onSelect: (connection: PlaceConnection) => void; onOpen: (item: MapItem) => void; onBack: () => void;
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3", PlaceHeading = headingLevel === 2 ? "h3" : "h4";
  const active = record.connections.findIndex(c => connectionKey(c) === selected), connection = record.connections[active];
  const focus = useRef<HTMLHeadingElement>(null), title = useRef<HTMLHeadingElement>(null);
  useEffect(() => { const target = focus.current ?? title.current; target?.closest(".map-place-panel")?.scrollTo?.({ top: 0, behavior: "instant" }); target?.focus({ preventScroll: true }); if (window.matchMedia("(max-width: 760px)").matches) target?.scrollIntoView({ block: "nearest" }); }, [selected, item.id]);
  function choose(c: PlaceConnection) { onSelect(c); }
  return <div className="map-journey">
    <button className="map-back" onClick={onBack}>← All records</button>
    <div className="map-journey-title">{item.image && <span className="map-journey-image"><MapImage key={item.image} src={item.image} alt={item.title} kind={item.kind} /></span>}<div><span className="map-record-kind"><MapSymbol kind={item.kind} />{mapKindNames[item.kind]}</span><Heading ref={title} tabIndex={-1}>{item.title}</Heading><button className="map-open-record" onClick={() => onOpen(item)}>Open full record</button></div></div>
    <nav className="map-journey-nav" aria-label="Documented place connections"><button aria-label="Previous connection" disabled={active <= 0} onClick={() => choose(record.connections[active - 1])}>←</button><span role="status">{active < 0 ? `${record.connections.length} connections` : `${active + 1} of ${record.connections.length} connections`}</span><button aria-label="Next connection" disabled={active >= record.connections.length - 1} onClick={() => choose(record.connections[active + 1])}>→</button></nav>
    {connection ? <div className="map-journey-current">
      <div className="map-journey-date">{connectionYears(connection).replace("Association dates unrecorded", "Date not recorded")}</div>
      <PlaceHeading ref={focus} tabIndex={-1}>{connection.place}</PlaceHeading>
      <p className="map-journey-relation">{relationLabel(connection.relation)}</p>
      <p className="map-journey-precision">{!connectionPlaceKey(connection) ? "Location unresolved · no map marker" : connection.precision === "country" ? "Country-level location" : connection.precision === "recorded point" ? "Recorded location · precision unverified" : "Approximate city / area"}</p>
      <details><summary>Source & location</summary><p>{connection.note}</p>{sourceHref(connection.sourceUrl) ? <a href={sourceHref(connection.sourceUrl)} target="_blank" rel="noreferrer">{connection.sourceLabel}</a> : <p>{connection.sourceLabel}</p>}</details>
    </div> : <p className="map-panel-intro">{!record.connections.length ? "No place connections match these years and place types. Adjust the filters or return to all records." : selected ? "That connection is outside this selection. Choose a place below." : "Choose a connection to locate it on the map."}</p>}
    <p className="map-journey-caption">Documented connections, in date order. Dates may overlap; unknown dates appear last.</p>
    <ol className="map-journey-list">{record.connections.map(c => <li key={connectionKey(c)}><button aria-pressed={connectionKey(c) === selected} onClick={() => choose(c)}><time>{connectionYears(c).replace("Association dates unrecorded", "Undated")}</time><strong>{c.place}</strong><span>{relationLabel(c.relation)}{!connectionPlaceKey(c) && " · unmapped"}</span></button></li>)}</ol>
    {record.truncated && <p className="map-panel-intro">Showing up to 32 matching connections. This record has more place evidence.</p>}
  </div>;
}
