"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { GeoJsonObject } from "geojson";
import type { PlaceGroup } from "@/lib/map";
import "leaflet/dist/leaflet.css";
import "./CatalogueMap.css";

export default function MapSurface({ groups, selected, onSelect }: { groups: PlaceGroup[]; selected: string; onSelect: (key: string) => void }) {
  const host = useRef<HTMLDivElement>(null), map = useRef<L.Map | null>(null);
  const choose = useRef(onSelect);
  useEffect(() => { choose.current = onSelect; }, [onSelect]);
  const [ready, setReady] = useState(false), [error, setError] = useState(false), [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!host.current) return;
    const controller = new AbortController();
    const instance = L.map(host.current, { center: [25, 10], zoom: 2, minZoom: 1, maxZoom: 7, scrollWheelZoom: false, worldCopyJump: false, maxBounds: [[-85, -200], [85, 200]], attributionControl: false, zoomAnimation: false, fadeAnimation: false });
    map.current = instance;
    L.control.attribution({ prefix: false }).addAttribution('<a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noreferrer">Natural Earth</a> · modern geography').addTo(instance);
    const resize = new ResizeObserver(() => instance.invalidateSize({ pan: false })); resize.observe(host.current);
    fetch("/maps/countries.geojson", { signal: controller.signal }).then(r => { if (!r.ok) throw Error("Map unavailable"); return r.json(); }).then((geo: GeoJsonObject) => {
      if (controller.signal.aborted) return;
      L.geoJSON(geo, { interactive: false, style: { color: "#8c887b", weight: 0.7, fillColor: "#e8e3d9", fillOpacity: 1 } }).addTo(instance);
      setReady(true); setError(false);
    }).catch(() => { if (!controller.signal.aborted) { setReady(true); setError(true); } });
    return () => { controller.abort(); resize.disconnect(); instance.remove(); map.current = null; setReady(false); };
  }, [retry]);
  useEffect(() => {
    const instance = map.current; if (!instance || !ready) return;
    const layer = L.layerGroup().addTo(instance);
    for (const g of groups) {
      const marker = L.marker([g.lat, g.lon], { keyboard: true, title: `${g.name}: ${g.entries.length} connections${g.country ? ", country only" : ""}`, alt: g.name,
        icon: L.divIcon({ className: `atlas-map-pin${g.country ? " is-country" : ""}${g.key === selected ? " is-selected" : ""}`, html: `<span>${g.entries.length}</span>`, iconSize: [44, 44], iconAnchor: [22, 22] }) }).addTo(layer);
      const label = document.createElement("span"); label.textContent = `${g.name}${g.country ? " · country only" : ""}`;
      marker.bindTooltip(label, { direction: "top", offset: [0, -22] }); marker.on("click", () => choose.current(g.key));
      const element = marker.getElement();
      element?.setAttribute("aria-label", `${g.name}: ${g.entries.length} place connections${g.country ? ", country only" : ""}`);
      element?.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); event.stopPropagation(); choose.current(g.key); }
      });
    }
    return () => { layer.remove(); };
  }, [groups, selected, ready]);
  const extent = groups.map(g => `${g.lat},${g.lon}`).join(";");
  useEffect(() => {
    if (!ready || !map.current) return;
    const points = extent.split(";").filter(Boolean).map(s => s.split(",").map(Number) as [number, number]);
    if (points.length) map.current.fitBounds(L.latLngBounds(points), { padding: [55, 55], maxZoom: 5, animate: false });
    else map.current.setView([25, 10], 2, { animate: false });
  }, [extent, ready]);
  function reset() {
    const points = groups.map(g => [g.lat, g.lon] as [number, number]);
    if (points.length) map.current?.fitBounds(L.latLngBounds(points), { padding: [55, 55], maxZoom: 5, animate: false });
    else map.current?.setView([25, 10], 2);
  }
  return <div className="catalogue-map-surface">
    <div ref={host} className="catalogue-map-geography" role="region" aria-label="Place map. Use arrow keys to pan, plus and minus to zoom. Places are also listed beside the map." />
    <button type="button" className="map-fit" onClick={reset}>Fit places</button>
    {error && <p className="map-surface-error" role="status">The background map could not load. Place details remain available. <button onClick={() => setRetry(v => v + 1)}>Retry map</button></p>}
  </div>;
}
