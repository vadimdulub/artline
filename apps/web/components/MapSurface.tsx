"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { Feature, GeoJsonObject, Polygon } from "geojson";
import { eventCountryGroups, type PlaceGroup } from "@/lib/map";
import "leaflet/dist/leaflet.css";
import "./CatalogueMap.css";

// Camera framing follows the polygon around the country's label point.
// Overseas components remain shaded, but do not push the main area offscreen.
function countryFocusBounds(feature: Feature, group: PlaceGroup): L.LatLngBounds {
  const geometry = feature.geometry;
  const polygons = geometry.type === "MultiPolygon" ? geometry.coordinates : geometry.type === "Polygon" ? [geometry.coordinates] : [];
  const parts = polygons.map(coordinates => {
    const shape: Polygon = { type: "Polygon", coordinates };
    return L.geoJSON(shape).getBounds();
  }).filter(bounds => bounds.isValid());
  const point = L.latLng(group.lat, group.lon);
  return parts.find(bounds => bounds.contains(point)) ?? parts.sort((a, b) => a.getCenter().distanceTo(point) - b.getCenter().distanceTo(point))[0] ?? L.latLngBounds([point]);
}

export default function MapSurface({ groups, selected, onSelect, highlightRegions = false }: { highlightRegions?: boolean; groups: PlaceGroup[]; selected: string; onSelect: (key: string) => void }) {
  const host = useRef<HTMLDivElement>(null), map = useRef<L.Map | null>(null);
  const geography = useRef<GeoJsonObject | null>(null);
  const regions = useRef<L.GeoJSON | null>(null);
  const regionFrames = useRef(new Map<string, L.LatLngBounds>());
  const fitAfterResize = useRef<() => void>(() => {});
  const choose = useRef(onSelect);
  useEffect(() => { choose.current = onSelect; }, [onSelect]);
  const [ready, setReady] = useState(false), [error, setError] = useState(false), [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!host.current) return;
    const controller = new AbortController();
    const instance = L.map(host.current, { center: [25, 10], zoom: 2, minZoom: 1, maxZoom: 7, scrollWheelZoom: false, worldCopyJump: false, maxBounds: [[-85, -200], [85, 200]], attributionControl: false, zoomAnimation: false, fadeAnimation: false });
    map.current = instance;
    L.control.attribution({ prefix: false }).addAttribution('<a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noreferrer">Natural Earth</a> · modern geography').addTo(instance);
    const resize = new ResizeObserver(() => { instance.invalidateSize({ pan: false }); fitAfterResize.current(); }); resize.observe(host.current);
    fetch("/maps/countries.geojson", { signal: controller.signal }).then(r => { if (!r.ok) throw Error("Map unavailable"); return r.json(); }).then((geo: GeoJsonObject) => {
      if (controller.signal.aborted) return;
      geography.current = geo;
      L.geoJSON(geo, { interactive: false, style: { color: "#8c887b", weight: 0.7, fillColor: "#e8e3d9", fillOpacity: 1 } }).addTo(instance);
      setReady(true); setError(false);
    }).catch(() => { if (!controller.signal.aborted) { setReady(true); setError(true); } });
    return () => { controller.abort(); resize.disconnect(); instance.remove(); map.current = null; geography.current = null; regions.current = null; setReady(false); };
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
  useEffect(() => {
    if (!map.current || !ready || !geography.current || !highlightRegions) return;
    const countries = eventCountryGroups(groups);
    const frames = regionFrames.current;
    const layer = L.geoJSON(geography.current, {
      filter: feature => countries.has(feature.properties?.code),
      style: feature => ({
        className: "map-event-region",
        color: countries.get(feature?.properties?.code)?.key === selected ? "#1b4332" : "#416451",
        weight: countries.get(feature?.properties?.code)?.key === selected ? 3 : 1.5,
        fillColor: countries.get(feature?.properties?.code)?.key === selected ? "#5d9272" : "#91a99a", fillOpacity: 0.8,
      }),
      onEachFeature: (feature, polygon) => {
        const group = countries.get(feature.properties?.code)!;
        frames.set(group.key, countryFocusBounds(feature, group));
        const label = document.createElement("span");
        label.textContent = `${group.name} · recorded event country · modern outline`;
        polygon.bindTooltip(label, { sticky: true });
        polygon.on("click", () => choose.current(group.key));
      },
    }).addTo(map.current);
    regions.current = layer;
    layer.eachLayer(polygon => {
      const path = polygon as L.Path & { feature?: { properties?: { code?: string } } };
      const group = countries.get(path.feature?.properties?.code ?? "");
      const element = path.getElement();
      if (!group || !element) return;
      element.setAttribute("tabindex", "0"); element.setAttribute("role", "button");
      element.setAttribute("aria-label", `${group.name} event region, modern country outline`);
      element.setAttribute("aria-pressed", String(group.key === selected));
      element.addEventListener("keydown", event => {
        const key = (event as KeyboardEvent).key;
        if (key === "Enter" || key === " ") { event.preventDefault(); event.stopPropagation(); choose.current(group.key); }
      });
    });
    return () => { layer.remove(); regions.current = null; frames.clear(); };
  }, [groups, selected, ready, highlightRegions]);
  const extent = groups.map(g => `${g.lat},${g.lon}`).join(";");
  const regionExtent = highlightRegions ? [...eventCountryGroups(groups).keys()].sort().join(",") : "";
  function reset() {
    const bounds = L.latLngBounds(groups.map(g => [g.lat, g.lon] as [number, number]));
    for (const frame of regionFrames.current.values()) bounds.extend(frame);
    if (bounds.isValid()) map.current?.fitBounds(bounds, { padding: [55, 55], maxZoom: 5, animate: false });
    else map.current?.setView([25, 10], 2, { animate: false });
  }
  useEffect(() => { fitAfterResize.current = reset; });
  useEffect(() => {
    if (ready) reset();
    // Geographic extents, not a selected marker, determine the full-map frame.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extent, regionExtent, ready]);
  useEffect(() => {
    if (!selected || !highlightRegions || !regions.current) return;
    const bounds = regionFrames.current.get(selected);
    if (bounds?.isValid()) map.current?.fitBounds(bounds, { padding: [45, 45], maxZoom: 5, animate: false });
  }, [selected, highlightRegions, ready, groups]);
  return <div className="catalogue-map-surface">
    <div ref={host} className="catalogue-map-geography" role="region" aria-label="Place map. Use arrow keys to pan, plus and minus to zoom. Places are also listed beside the map." />
    <button type="button" className="map-fit" onClick={reset}>Fit places</button>
    {error && <p className="map-surface-error" role="status">The background map could not load. Place details remain available. <button onClick={() => setRetry(v => v + 1)}>Retry map</button></p>}
  </div>;
}
