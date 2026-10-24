"use client";
import type { CSSProperties } from "react";
import { connectionKey, connectionYears, groupPlaceConnections, relationLabel, type MapItem, type PlaceConnection, type PlaceGroup } from "@/lib/map";
import { MapImage } from "./MapVisuals";

export function MapPlaceChoices({ groups, onSelect, onZoom, onPreview, colorStyle, selectedRecord, selectedStop }: {
  groups: PlaceGroup[];
  onSelect: (item: MapItem, connection: PlaceConnection) => void;
  onZoom: () => void;
  onPreview: (record: string) => void;
  colorStyle: (item: MapItem) => CSSProperties;
  selectedRecord: string;
  selectedStop: string;
}) {
  const multipleCoordinates = new Set(groups.map(group => `${group.lat},${group.lon}`)).size > 1;
  return <section className="map-place-choices" aria-label="Place connections">
    {multipleCoordinates && <div className="map-choice-actions">
      <button type="button" className="map-choice-zoom" onClick={onZoom}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5" /></svg>Zoom to these places</button>
    </div>}
    {groupPlaceConnections(groups).map(({ item, connections }) => {
      const record = `${item.kind}:${item.id}`;
      const metadata = [item.kind !== "artist" ? item.context : undefined, item.years].filter(Boolean).join(" · ");
      return <section className="map-choice-record" key={record} aria-label={item.title} style={colorStyle(item)}
        onMouseEnter={() => onPreview(record)} onMouseLeave={() => onPreview("")} onFocusCapture={() => onPreview(record)} onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) onPreview(""); }}>
        <button type="button" className={`map-choice-record-title${item.image ? " has-image" : ""}`} aria-label={`Details for ${item.title}`} onClick={() => onSelect(item, connections[0])}>
          {item.image && <span className="map-choice-image" aria-hidden="true"><MapImage key={item.image} src={item.image} alt="" kind={item.kind} compact /></span>}
          <span><strong>{item.title}</strong>{metadata && <small>{metadata}</small>}</span>
        </button>
        <ol className="map-choice-timeline" aria-label={`Connections for ${item.title}`}>
          {connections.map(connection => {
            const dated = connection.start !== null || connection.end !== null || Boolean(connection.dateDisplay);
            const years = dated ? connectionYears(connection) : "Date not recorded";
            const relation = relationLabel(connection.relation);
            const separator = /\b(in|at|near|to|of)$/i.test(relation) ? " " : ": ";
            return <li className="map-choice-milestone" data-dated={dated} key={connectionKey(connection)}>
              <button type="button" aria-label={`${item.title}, ${connection.place}, ${relationLabel(connection.relation)}, ${years}`}
                aria-current={record === selectedRecord && connectionKey(connection) === selectedStop ? "true" : undefined} onClick={() => onSelect(item, connection)}>
                <span className="map-choice-milestone-fact">{relation}{separator}<strong>{connection.place}</strong></span>
                {dated ? <time>{years}</time> : <small>{years}</small>}
              </button>
            </li>;
          })}
        </ol>
      </section>;
    })}
  </section>;
}
