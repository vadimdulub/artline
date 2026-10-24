"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { connectionKey, connectionPlaceKey, connectionYears, mapKindNames, relationLabel, sourceHref, type MapItem, type MapRecord, type PlaceConnection } from "@/lib/map";
import { MapImage } from "./MapVisuals";

export function MapRecordJourney({ item, record, selected, headingLevel, onSelect, onOpen, onLocate, actions, autoFocus = true }: {
  item: MapItem; record: MapRecord; selected: string; headingLevel: 2 | 3;
  onSelect: (connection: PlaceConnection) => void; onOpen: (item: MapItem) => void; onLocate?: () => void; actions?: ReactNode; autoFocus?: boolean;
}) {
  const Heading = headingLevel === 2 ? "h2" : "h3", PlaceHeading = headingLevel === 2 ? "h3" : "h4";
  const active = record.connections.findIndex(connection => connectionKey(connection) === selected);
  const connection = record.connections[active], multiple = record.connections.length > 1;
  const focus = useRef<HTMLHeadingElement>(null), title = useRef<HTMLHeadingElement>(null);
  const date = connection ? connectionYears(connection).replace("Association dates unrecorded", "Date not recorded") : "";
  const metadata = [item.kind !== "artist" && item.context !== mapKindNames[item.kind] ? item.context : undefined, item.years !== date ? item.years : undefined].filter(Boolean).join(" · ");
  const precision = !connection ? "" : !connectionPlaceKey(connection) ? "Location unresolved · no map marker" : connection.precision === "country" ? "Country-level location" : connection.precision === "recorded point" ? "Recorded location · precision unverified" : "Approximate city / area";
  const recordAction = `View ${mapKindNames[item.kind].toLowerCase()}`;
  useEffect(() => {
    if (!autoFocus) return;
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement && activeElement.closest("input,select,textarea,summary,.map-painter-picker")) return;
    if (activeElement instanceof HTMLElement && activeElement !== document.body && !activeElement.closest(".map-layer-panel,.map-place-panel,.atlas-map-pin")) return;
    const target = focus.current ?? title.current;
    target?.closest(".map-details-body")?.scrollTo?.({ top: 0, behavior: "instant" });
    target?.focus({ preventScroll: true });
  }, [selected, item.id, autoFocus]);

  return <div className="map-journey">
    <div className="map-journey-title">
      {item.image && <span className="map-journey-image"><MapImage key={item.image} src={item.image} alt={item.title} kind={item.kind} /></span>}
      <div className="map-journey-identity"><Heading ref={title} tabIndex={-1}>{item.title}</Heading>{metadata && <p className="map-record-meta">{metadata}</p>}</div>
      {actions && <div className="map-record-actions">{actions}</div>}
    </div>
    {connection ? <div className="map-journey-current">
      {(connection.start !== null || connection.end !== null || Boolean(connection.dateDisplay)) && <div className="map-journey-date">{date}</div>}
      <div className="map-journey-place-heading"><PlaceHeading ref={focus} tabIndex={-1}>{connection.place}</PlaceHeading>{onLocate && <button type="button" className="map-locate-place" aria-label={`Find on map: ${connection.place}`} onClick={onLocate}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2v3m0 14v3M2 12h3m14 0h3M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" /></svg><span>Find on map</span></button>}</div>
      <p className="map-journey-relation">{relationLabel(connection.relation)}</p>
      <p className="map-journey-precision">{precision}</p>
      <details className="map-source"><summary>Source & location</summary>
        {connection.note && <p>{connection.note}</p>}
        {sourceHref(connection.sourceUrl) ? <a href={sourceHref(connection.sourceUrl)} target="_blank" rel="noreferrer">{connection.sourceLabel || "View source"}</a> : connection.sourceLabel && <p>{connection.sourceLabel}</p>}
      </details>
    </div> : <p className="map-panel-intro">{!record.connections.length ? "No documented places are available for this record." : selected ? "That connection is outside this selection. Choose a place below." : "Choose a connection to locate it on the map."}</p>}
    <button className="map-full-record" onClick={() => onOpen(item)}>{recordAction}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></button>
    {multiple && <nav className="map-journey-nav" aria-label="Documented place connections">
      <button aria-label="Previous connection" disabled={active <= 0} onClick={() => onSelect(record.connections[active - 1])}>←</button>
      <span role="status">{active < 0 ? `${record.connections.length} connections` : `${active + 1} / ${record.connections.length}`}</span>
      <button aria-label="Next connection" disabled={active >= record.connections.length - 1} onClick={() => onSelect(record.connections[active + 1])}>→</button>
    </nav>}
    {(multiple || (active < 0 && record.connections.length > 0)) && <details key={`${item.kind}:${item.id}`} className="map-journey-history" open={active < 0}>
      <summary>Documented places</summary>
      <p className="map-journey-caption">In recorded date order. Dates may overlap; unknown dates appear last.</p>
      <ol className="map-journey-list">{record.connections.map(connection => <li key={connectionKey(connection)}><button aria-label={`${connection.place}, ${connectionYears(connection)}, ${relationLabel(connection.relation)}${!connectionPlaceKey(connection) ? ", location unresolved" : ""}`} aria-pressed={connectionKey(connection) === selected} onClick={() => onSelect(connection)}><time>{connectionYears(connection).replace("Association dates unrecorded", "Undated")}</time><strong>{connection.place}</strong><span>{relationLabel(connection.relation)}{!connectionPlaceKey(connection) && " · unmapped"}</span></button></li>)}</ol>
    </details>}
    {record.truncated && <p className="map-panel-intro">Showing up to 32 matching connections.</p>}
  </div>;
}
