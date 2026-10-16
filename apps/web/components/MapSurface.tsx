"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { Feature, FeatureCollection, Polygon } from "geojson";
import { clusterPlaces, eventCountryGroups, mapSymbolPaths, placeKind, placeRecordCount, type PlaceGroup } from "@/lib/map";
import { LoadingIndicator } from "./LoadingIndicator";
import "leaflet/dist/leaflet.css";
import "./CatalogueMap.css";

// Focus the component around the label point; keep overseas polygons available.
function countryFocusBounds(feature: Feature, group: PlaceGroup): L.LatLngBounds {
  const geometry = feature.geometry;
  const polygons = geometry.type === "MultiPolygon" ? geometry.coordinates : geometry.type === "Polygon" ? [geometry.coordinates] : [];
  const parts = polygons.map(coordinates => { const shape: Polygon = { type: "Polygon", coordinates }; return L.geoJSON(shape).getBounds(); }).filter(bounds => bounds.isValid());
  const point = L.latLng(group.lat, group.lon);
  return parts.find(bounds => bounds.contains(point)) ?? parts.sort((a, b) => a.getCenter().distanceTo(point) - b.getCenter().distanceTo(point))[0] ?? L.latLngBounds([point]);
}
function symbol(group: PlaceGroup): SVGSVGElement {
  const ns = "http://www.w3.org/2000/svg", svg = document.createElementNS(ns, "svg");
  for (const [key, value] of Object.entries({ viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.5", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" })) svg.setAttribute(key, value);
  for (const d of mapSymbolPaths[placeKind(group)]) { const path = document.createElementNS(ns, "path"); path.setAttribute("d", d); svg.append(path); }
  return svg;
}
function activate(element: Element | undefined, action: () => void) {
  element?.addEventListener("keydown", event => {
    const key = (event as KeyboardEvent).key;
    if (key === "Enter" || key === " ") { event.preventDefault(); event.stopPropagation(); action(); }
  });
}

export default function MapSurface({ groups, selected, hovered = "", onSelect, onReset, highlightRegions = false, busy = false }: {
  groups: PlaceGroup[]; selected: string; hovered?: string; onSelect: (key: string) => void; onReset: () => void; highlightRegions?: boolean; busy?: boolean;
}) {
  const host = useRef<HTMLDivElement>(null), map = useRef<L.Map | null>(null);
  const geography = useRef<FeatureCollection | null>(null);
  const regionFrames = useRef(new Map<string, L.LatLngBounds>());
  const markerElements = useRef<{ element: HTMLElement; keys: string[] }[]>([]);
  const fitAfterResize = useRef<() => void>(() => {}), choose = useRef(onSelect), hover = useRef(hovered);
  const [ready, setReady] = useState(false), [error, setError] = useState(false), [retry, setRetry] = useState(0);
  useEffect(() => { choose.current = onSelect; }, [onSelect]);
  useEffect(() => { hover.current = hovered; for (const { element, keys } of markerElements.current) element.classList.toggle("is-hovered", keys.includes(hovered)); }, [hovered]);
  useEffect(() => {
    if (!host.current) return;
    const controller = new AbortController();
    const instance = L.map(host.current, { center: [25, 10], zoom: 2, minZoom: 1, maxZoom: 7, scrollWheelZoom: false, worldCopyJump: false, maxBounds: [[-85, -200], [85, 200]], attributionControl: false, zoomControl: false, zoomAnimation: false, fadeAnimation: false });
    map.current = instance;
    L.control.zoom({ position: "bottomleft" }).addTo(instance);
    L.control.attribution({ prefix: false }).addAttribution('<a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noreferrer">Natural Earth</a> · modern boundaries').addTo(instance);
    const resize = new ResizeObserver(() => { instance.invalidateSize({ pan: false }); fitAfterResize.current(); }); resize.observe(host.current);
    fetch("/maps/countries.geojson", { signal: controller.signal }).then(r => { if (!r.ok) throw Error("Map unavailable"); return r.json(); }).then((geo: FeatureCollection) => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(geo.features)) throw Error("Invalid map");
      geography.current = geo;
      L.geoJSON(geo, { interactive: false, style: { color: "#b4b7ac", weight: 0.8, fillColor: "#f2efe8", fillOpacity: 1 } }).addTo(instance);
      setReady(true); setError(false);
    }).catch(() => { if (!controller.signal.aborted) { setReady(true); setError(true); } });
    return () => { controller.abort(); resize.disconnect(); instance.remove(); map.current = null; geography.current = null; setReady(false); };
  }, [retry]);

  useEffect(() => {
    const instance = map.current; if (!instance || !ready || busy) return;
    const places = L.layerGroup().addTo(instance), labels = L.layerGroup().addTo(instance);
    function draw() {
      places.clearLayers(); labels.clearLayers(); markerElements.current = [];
      const size = instance!.getSize();
      const clusters = clusterPlaces(groups, g => instance!.latLngToContainerPoint([g.lat, g.lon]), 72, selected)
        .sort((a, b) => Number(b.groups.some(g => g.key === selected)) - Number(a.groups.some(g => g.key === selected)));
      const occupied: { x: number; y: number; width: number; height: number }[] = [
        { x: 10, y: 10, width: 132, height: 48 },
        { x: 10, y: size.y - 150, width: 48, height: 94 },
        { x: 10, y: size.y - 46, width: 238, height: 32 },
      ];
      for (const cluster of clusters) {
        if (cluster.x < -180 || cluster.y < -60 || cluster.x > size.x + 60 || cluster.y > size.y + 60) continue;
        const grouped = cluster.groups.length > 1, g = cluster.groups[0], count = placeRecordCount(g);
        const content = document.createElement("span"); content.className = "map-marker-label";
        const glyph = document.createElement("span"); glyph.className = "map-marker-symbol";
        if (grouped) glyph.textContent = String(cluster.groups.length); else glyph.append(symbol(g));
        const name = document.createElement("span"); name.className = "map-marker-name"; name.textContent = grouped ? `${g.name} +${cluster.groups.length - 1}` : g.name;
        content.append(glyph, name);
        if (!grouped && count > 1) { const badge = document.createElement("span"); badge.className = "map-marker-count"; badge.textContent = String(count); content.append(badge); }
        const title = grouped ? `${cluster.groups.length} nearby places: ${cluster.groups.map(place => place.name).join(", ")}. Zoom in to explore.` : `${g.name}: ${count} ${count === 1 ? "record" : "records"}${g.country ? ", country-level location" : ", city or area"}`;
        const marker = L.marker([g.lat, g.lon], { keyboard: true, title, alt: g.name, zIndexOffset: g.key === selected ? 1000 : 0,
          icon: L.divIcon({ className: `atlas-map-pin is-${placeKind(g)}${grouped ? " is-cluster" : g.country ? " is-country" : ""}${g.key === selected ? " is-selected" : ""}`, html: content, iconSize: [44, 44], iconAnchor: [22, 22] }) }).addTo(places);
        // Offset colliding labels, never the place coordinate. A short leader
        // joins the displaced label to its actual approximate map position.
        const { width: labelWidth, height: labelHeight } = content.getBoundingClientRect();
        const preferredX = Math.max(12 - (cluster.x - 22), Math.min(0, size.x - 12 - (cluster.x - 22 + labelWidth)));
        const leftX = Math.max(12 - (cluster.x - 22), 44 - labelWidth);
        const candidates = [0, -58, 58, -116, 116, -174, 174, -232, 232].flatMap(y => [preferredX, leftX].map(x => ({ x, y })));
        const offset = candidates.find(offset => {
          const x = cluster.x - 22 + offset.x, y = cluster.y - 22 + offset.y;
          return y >= 10 && y + labelHeight < size.y - 28 && !occupied.some(r => x < r.x + r.width + 8 && x + labelWidth > r.x - 8 && y < r.y + r.height + 6 && y + labelHeight > r.y - 6);
        }) ?? { x: preferredX, y: 0 };
        const offsetX = offset.x, offsetY = offset.y;
        if (offsetX || offsetY) {
          content.style.transform = `translate(${offsetX}px, ${offsetY}px)`;
          if (!grouped) {
            const anchor = instance!.containerPointToLatLng([cluster.x + offsetX, cluster.y + offsetY]);
            L.polyline([[g.lat, g.lon], anchor], { interactive: false, color: "#625d55", weight: 1, opacity: 0.7 }).addTo(places);
            L.circleMarker([g.lat, g.lon], { interactive: false, radius: 3, weight: 1, color: "#625d55", fillColor: "#faf8f3", fillOpacity: 1 }).addTo(places);
          }
        }
        function select() {
          if (!grouped) { choose.current(g.key); return; }
          const canSeparate = clusterPlaces(cluster.groups, place => instance!.project([place.lat, place.lon], 7), 72).length > 1;
          if (instance!.getZoom() < 7 && canSeparate) {
            instance!.fitBounds(L.latLngBounds(cluster.groups.map(p => [p.lat, p.lon] as [number, number])), { padding: [70, 70], maxZoom: 7, animate: false });
            instance!.getContainer().focus({ preventScroll: true });
          } else {
            const options = document.createElement("div"); options.className = "map-cluster-choices";
            const heading = document.createElement("strong"); heading.textContent = "Choose a place"; options.append(heading);
            cluster.groups.forEach(place => { const button = document.createElement("button"); button.textContent = `${place.name}${place.country ? " · country" : " · local area"}`; button.onclick = () => { instance!.closePopup(); choose.current(place.key); }; options.append(button); });
            const popup = L.popup({ maxWidth: 260 }).setLatLng([g.lat, g.lon]).setContent(options).openOn(instance!);
            popup.once("remove", () => instance!.getContainer().focus({ preventScroll: true }));
            options.querySelector("button")?.focus();
          }
        }
        marker.on("click", select);
        const element = marker.getElement(); element?.setAttribute("aria-label", title); element?.setAttribute("aria-pressed", String(!grouped && g.key === selected)); activate(element, select);
        if (element) { const keys = cluster.groups.map(p => p.key); markerElements.current.push({ element, keys }); element.classList.toggle("is-hovered", keys.includes(hover.current)); }
        occupied.push({ x: cluster.x - 22 + offsetX, y: cluster.y - 22 + offsetY, width: labelWidth, height: labelHeight });
      }
      // Background labels orient the reader; they never geocode a record.
      for (const feature of [...(geography.current?.features ?? [])].sort((a,b) => (a.properties?.rank ?? 9) - (b.properties?.rank ?? 9))) {
        const p = feature.properties;
        if (!p || !Number.isFinite(p.lat) || !Number.isFinite(p.lon) || (instance!.getZoom() < 3 && p.rank > 2)) continue;
        const point = instance!.latLngToContainerPoint([p.lat, p.lon]), width = Math.min(140, p.name.length * 7 + 10);
        const rect = { x: point.x - width / 2, y: point.y - 10, width, height: 20 };
        if (rect.x < 12 || rect.y < 16 || rect.x + width > size.x - 12 || rect.y > size.y - 38) continue;
        if (occupied.some(r => rect.x < r.x + r.width + 12 && rect.x + width > r.x - 12 && rect.y < r.y + r.height + 5 && rect.y + 20 > r.y - 5)) continue;
        const label = document.createElement("span"); label.textContent = p.name;
        const marker = L.marker([p.lat, p.lon], { interactive: false, keyboard: false, icon: L.divIcon({ className: "map-country-label", html: label, iconSize: [width, 20], iconAnchor: [width / 2, 10] }) }).addTo(labels);
        marker.getElement()?.setAttribute("aria-hidden", "true"); occupied.push(rect);
      }
    }
    draw(); instance.on("moveend zoomend", draw);
    return () => { instance.off("moveend zoomend", draw); places.remove(); labels.remove(); markerElements.current = []; };
  }, [groups, selected, ready, busy]);

  useEffect(() => {
    if (!map.current || !ready || !geography.current || !highlightRegions || busy) return;
    const countries = eventCountryGroups(groups), frames = regionFrames.current;
    const layer = L.geoJSON(geography.current, {
      filter: feature => countries.has(feature.properties?.code),
      style: feature => ({ className: "map-event-region", color: countries.get(feature?.properties?.code)?.key === selected ? "#315b40" : "#6f9179", weight: countries.get(feature?.properties?.code)?.key === selected ? 2.5 : 1.5, fillColor: "#91b29b", fillOpacity: countries.get(feature?.properties?.code)?.key === selected ? 0.8 : 0.48 }),
      onEachFeature: (feature, polygon) => {
        const group = countries.get(feature.properties?.code)!; frames.set(group.key, countryFocusBounds(feature, group));
        const label = document.createElement("span"); label.textContent = `${group.name} · event region · modern country outline`;
        polygon.bindTooltip(label, { sticky: true }); polygon.on("click", () => choose.current(group.key));
      },
    }).addTo(map.current);
    layer.eachLayer(polygon => {
      const path = polygon as L.Path & { feature?: { properties?: { code?: string } } };
      const group = countries.get(path.feature?.properties?.code ?? ""), element = path.getElement();
      if (!group || !element) return;
      element.setAttribute("tabindex", "0"); element.setAttribute("role", "button"); element.setAttribute("aria-label", `${group.name} event region, modern country outline`); element.setAttribute("aria-pressed", String(group.key === selected)); activate(element, () => choose.current(group.key));
    });
    return () => { layer.remove(); frames.clear(); };
  }, [groups, selected, ready, highlightRegions, busy]);
  const extent = groups.map(g => `${g.lat},${g.lon}`).join(";");
  const regionExtent = highlightRegions ? [...eventCountryGroups(groups).keys()].sort().join(",") : "";
  function reset() {
    if (busy) return;
    const bounds = L.latLngBounds(groups.map(g => [g.lat, g.lon] as [number, number]));
    for (const frame of regionFrames.current.values()) bounds.extend(frame);
    if (bounds.isValid()) map.current?.fitBounds(bounds, { padding: [64, 70], maxZoom: 5, animate: false });
    else map.current?.setView([25, 10], 2, { animate: false });
  }
  function focus() {
    const group = groups.find(g => g.key === selected); if (!group || busy || !map.current) return;
    const code = group.entries.find(e => e.connection.countryCode)?.connection.countryCode;
    const feature = code && geography.current?.features.find(f => f.properties?.code === code);
    if (group.country && feature) map.current.fitBounds(countryFocusBounds(feature, group), { padding: [60, 60], maxZoom: 5, animate: false });
    else map.current.setView([group.lat, group.lon], Math.max(5, map.current.getZoom()), { animate: false });
  }
  useEffect(() => { fitAfterResize.current = () => selected ? focus() : reset(); });
  useEffect(() => {
    if (ready && !busy) reset();
    // Extent changes frame the current result page, not a hover or selected marker.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [extent, regionExtent, ready, busy]);
  useEffect(() => {
    if (ready && !busy) focus();
    // Selection has its own camera target; source metadata changes don't reframe it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, ready, busy]);
  return <div className="catalogue-map-surface">
    <div ref={host} inert={busy} className="catalogue-map-geography" role="region" aria-label="Place map. Use arrow keys to pan, plus and minus to zoom. Places are also listed beside the map." />
    <button type="button" className="map-fit" disabled={busy || !ready} onClick={() => { reset(); onReset(); }}>Show all places</button>
    {!ready && <div className="map-surface-loading"><LoadingIndicator label="Loading the map…" /></div>}
    {error && <p className="map-surface-error" role="status">The background map could not load. Place details remain available. <button onClick={() => setRetry(v => v + 1)}>Retry map</button></p>}
  </div>;
}
