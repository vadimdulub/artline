"use client";
import "./CatalogueMap.css";
export function MapViewSwitch({ map, onChange }: { map: boolean; onChange: (map: boolean) => void }) {
  return <div className="map-view-switch" role="group" aria-label="Explore by time or place">
    <button type="button" aria-pressed={!map} onClick={() => onChange(false)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 7h12M8 12h13M3 17h14" /></svg>Timeline</button>
    <button type="button" aria-pressed={map} onClick={() => onChange(true)}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2V5Zm6-2v16m6-14v16" /></svg>Map</button>
  </div>;
}
