"use client";
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import type { Feature, FeatureCollection, Polygon } from "geojson";
import { mapIdentity, type MapIdentityColor } from "@/lib/map-colors";
import { clusterPlaces, connectionYears, eventCountryGroups, mapSymbolPaths, placeKind, type PlaceGroup } from "@/lib/map";
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

export default function MapSurface({ groups, selected, hovered = "", previewRecord = "", selectedRecord = "", onSelect, onCluster, onEventSelect, colors, focusSelection = false, highlightRegions = false, busy = false, detailsVisible = false, focusRequest }: {
  groups: PlaceGroup[]; selected: string; hovered?: string; previewRecord?: string; selectedRecord?: string; onSelect: (key: string) => void; onCluster: (keys: string[]) => void; onEventSelect?: (key: string, record?: string) => void; colors: Record<string, MapIdentityColor>; focusSelection?: boolean; highlightRegions?: boolean; busy?: boolean; detailsVisible?: boolean; focusRequest?: { keys: string[]; revision: number };
}) {
  const host = useRef<HTMLDivElement>(null), map = useRef<L.Map | null>(null);
  const geography = useRef<FeatureCollection | null>(null);
  const regionFrames = useRef(new Map<string, L.LatLngBounds>());
  const markerElements = useRef<{ element: HTMLElement; keys: string[]; records: string[] }[]>([]);
  const choose = useRef(onSelect), chooseCluster = useRef(onCluster), hover = useRef({ place: hovered, record: previewRecord }), framed = useRef(false), inspected = useRef("");
  const chooseEvent = useRef(onEventSelect);
  const [panOpen, setPanOpen] = useState(false);
  const handledFocus = useRef(0);
  const [ready, setReady] = useState(false), [error, setError] = useState(false), [retry, setRetry] = useState(0);
  useEffect(() => { choose.current = onSelect; chooseCluster.current = onCluster; chooseEvent.current = onEventSelect; }, [onSelect, onCluster, onEventSelect]);
  useEffect(() => {
    hover.current = { place: hovered, record: previewRecord };
    for (const { element, keys, records } of markerElements.current) element.classList.toggle("is-hovered", keys.includes(hovered) || records.includes(previewRecord));
  }, [hovered, previewRecord]);
  useEffect(() => {
    if (!host.current) return;
    const controller = new AbortController();
    const instance = L.map(host.current, { center: [25, 10], zoom: 2, minZoom: 1, maxZoom: 10, scrollWheelZoom: true, worldCopyJump: false, maxBounds: [[-85, -200], [85, 200]], attributionControl: false, zoomControl: false, zoomAnimation: false, fadeAnimation: false });
    map.current = instance;
    L.control.attribution({ prefix: false }).addAttribution('<a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noreferrer">Natural Earth</a> · modern boundaries').addTo(instance);
    L.control.scale({ position: "bottomright", imperial: false, maxWidth: 100 }).addTo(instance);
    const resize = new ResizeObserver(() => { instance.invalidateSize({ pan: false }); }); resize.observe(host.current);
    fetch("/maps/countries.geojson", { signal: controller.signal }).then(r => { if (!r.ok) throw Error("Map unavailable"); return r.json(); }).then((geo: FeatureCollection) => {
      if (controller.signal.aborted) return;
      if (!Array.isArray(geo.features)) throw Error("Invalid map");
      geography.current = geo;
      const theme = getComputedStyle(host.current!);
      L.geoJSON(geo, { interactive: false, style: { color: theme.getPropertyValue("--map-coast").trim() || "#3b443e", weight: 0.7, fillColor: theme.getPropertyValue("--map-land").trim() || "#252b28", fillOpacity: 1 } }).addTo(instance);
      setReady(true); setError(false);
    }).catch(() => { if (!controller.signal.aborted) { setReady(true); setError(true); } });
    return () => { controller.abort(); resize.disconnect(); instance.remove(); map.current = null; geography.current = null; setReady(false); };
  }, [retry]);

  useEffect(() => {
    const instance = map.current; if (!instance || !ready || busy) return;
    const places = L.layerGroup().addTo(instance), labels = L.layerGroup().addTo(instance);
    function draw() {
      const focused = document.activeElement?.closest<HTMLElement>(".atlas-map-pin")?.dataset.placeKeys?.split("|")[0];
      places.clearLayers(); labels.clearLayers(); markerElements.current = [];
      const size = instance!.getSize();
      let illustrated = 0;
      const illustrationLimit = size.x >= 900 ? 3 : size.x >= 600 ? 2 : 1;
      // 64 px also separates diagonal 44 × 44 px hit areas.
      const clusters = clusterPlaces(groups, group => instance!.latLngToContainerPoint([group.lat, group.lon]), 64, selected);
      const occupied = clusters.map(cluster => ({ x: cluster.x - 22, y: cluster.y - 22, width: 44, height: 44 }));
      occupied.push({ x: 0, y: size.y - 26, width: 260, height: 26 });
      const root = host.current!.closest(".map-workspace"), panel = root?.querySelector<HTMLElement>(".map-place-panel:not([hidden])");
      const bounds = host.current!.getBoundingClientRect(), panelBounds = panel?.getBoundingClientRect();
      for (const controls of host.current!.closest(".map-canvas-wrap")!.querySelectorAll<HTMLElement>(".map-navigation-controls,.map-direction-controls,.map-workspace-toolbar,.map-guide>summary,.leaflet-control-scale")) {
        const rect = controls.getBoundingClientRect(); occupied.push({ x: rect.left - bounds.left, y: rect.top - bounds.top, width: rect.width, height: rect.height });
      }
      if (panelBounds && panelBounds.top > bounds.top && panelBounds.top < bounds.bottom) occupied.push({ x: 0, y: panelBounds.top - bounds.top, width: size.x, height: bounds.bottom - panelBounds.top });
      for (const cluster of clusters.sort((a,b) => Number(b.groups.some(group => group.key === selected)) - Number(a.groups.some(group => group.key === selected)))) {
        if (cluster.x < -22 || cluster.y < -22 || cluster.x > size.x + 22 || cluster.y > size.y + 22) continue;
        const grouped = cluster.groups.length > 1, group = cluster.groups[0], active = cluster.groups.some(place => place.key === selected);
        const entries = cluster.groups.flatMap(place => place.entries), owners = [...new Set(entries.map(entry => mapIdentity(entry.item)))];
        const color = colors[owners[0]], mixed = owners.length > 1, connections = entries.length;
        const imageEntry = illustrated < illustrationLimit ? entries.find(entry => entry.item.image && `${entry.item.kind}:${entry.item.id}` === selectedRecord) ?? entries.find(entry => entry.item.image) : undefined;
        const recordNames = [...new Set(entries.map(entry => entry.item.title))], placeNames = [...new Set(entries.map(entry => entry.connection.place))];
        const uniqueItems = [...new Map(entries.map(entry => [`${entry.item.kind}:${entry.item.id}`, entry.item])).values()];
        const sameKind = uniqueItems.every(item => item.kind === uniqueItems[0].kind);
        const kindNames = { artist: "creators", artwork: "artworks", book: "books", event: "events" };
        const caption = imageEntry?.item.title ?? (recordNames.length === 1 ? recordNames[0] : placeNames.slice(0, 2).join(" / "));
        const title = entries.length > 1 ? `${caption}. ${connections} connections: ${placeNames.slice(0,4).join(", ")}. Choose a connection.` : `${entries[0].item.title}, ${entries[0].connection.place}, ${entries[0].connection.relation}, ${connectionYears(entries[0].connection)}`;
        const content = document.createElement("span"); content.className = "map-marker-root";
        const glyph = document.createElement("span"); glyph.className = "map-marker-symbol";
        if (grouped || entries.length > 1) glyph.textContent = String(connections); else glyph.append(symbol(group));
        const label = document.createElement("span"); label.className = "map-marker-label";
        if (imageEntry?.item.image) {
          label.classList.add("has-artwork");
          const reproduction = document.createElement("img"); reproduction.className = "map-marker-artwork";
          reproduction.src = imageEntry.item.image; reproduction.alt = imageEntry.item.title; reproduction.decoding = "async";
          reproduction.addEventListener("error", () => { reproduction.hidden = true; label.classList.remove("has-artwork"); }, { once: true });
          label.append(reproduction);
        }
        const name = document.createElement("span"); name.className = "map-marker-name";
        name.textContent = caption;
        const context = document.createElement("small"); context.textContent = imageEntry && uniqueItems.length > 1 ? `${uniqueItems.length} ${sameKind ? kindNames[uniqueItems[0].kind] : "items"} · ${placeNames.length > 1 ? `${placeNames.length} places` : placeNames[0]}` : imageEntry && entries.length > 1 ? `${placeNames.length > 1 ? `${placeNames.length} places` : placeNames[0]} · ${connections} connections` : recordNames.length === 1 ? placeNames.slice(0,2).join(" / ") : recordNames.slice(0,2).join(" / ");
        if (mixed) { const swatches = document.createElement("span"); swatches.className = "map-marker-swatches"; for (const owner of owners) { const swatch = document.createElement("i"); swatch.style.background = colors[owner]?.hex ?? "#625d55"; swatches.append(swatch); } label.append(swatches); }
        label.append(name, context); content.append(glyph, label);
        const marker = L.marker([group.lat, group.lon], { keyboard: true, title, alt: group.name, zIndexOffset: active ? 1000 : 0,
          icon: L.divIcon({ className: `atlas-map-pin is-${placeKind(group)}${grouped ? " is-cluster" : group.country ? " is-country" : ""}${mixed ? " is-mixed" : ""}${active ? " is-selected" : ""}`, html: content, iconSize: [44,44], iconAnchor: [22,22] }) }).addTo(places);
        const element = marker.getElement();
        element?.style.setProperty("--map-identity", mixed ? "#625d55" : color?.hex ?? "#625d55");
        element?.style.setProperty("--map-identity-fill", mixed ? "#faf8f3" : color?.fill ?? "#faf8f3");
        function arrangeCaption() {
          const { width, height } = label.getBoundingClientRect();
          const captionGap = label.classList.contains("has-artwork") ? 34 : 28;
          const candidates = [0,-26,26,-44,44].flatMap(offset => [cluster.x + captionGap, cluster.x - captionGap - width].map(x => ({ x, y: cluster.y - height / 2 + offset })));
          candidates.push({ x: cluster.x - width / 2, y: cluster.y - height - 30 }, { x: cluster.x - width / 2, y: cluster.y + 30 });
          const placement = candidates.find(({ x,y }) => {
            const ex = Math.max(x, Math.min(x + width, cluster.x)), ey = Math.max(y, Math.min(y + height, cluster.y));
            return x >= 8 && x + width <= size.x - 8 && y >= 8 && y + height < size.y - 26 && Math.hypot(ex-cluster.x,ey-cluster.y) <= 56 && !occupied.some(rect => x < rect.x + rect.width + 5 && x + width > rect.x - 5 && y < rect.y + rect.height + 5 && y + height > rect.y - 5);
          });
          return { placement, width, height };
        }
        let layout = arrangeCaption();
        if (!layout.placement && imageEntry) {
          label.querySelector("img")?.remove(); label.classList.remove("has-artwork");
          name.textContent = recordNames.length === 1 ? recordNames[0] : placeNames.slice(0, 2).join(" / ");
          context.textContent = recordNames.length === 1 ? placeNames.slice(0, 2).join(" / ") : recordNames.slice(0, 2).join(" / ");
          layout = arrangeCaption();
        }
        const { placement, width, height } = layout;
        if (placement) {
          if (label.classList.contains("has-artwork")) illustrated++;
          label.style.left = `${placement.x - cluster.x + 22}px`; label.style.top = `${placement.y - cluster.y + 22}px`;
          occupied.push({ ...placement, width, height });
          const ex = Math.max(placement.x, Math.min(placement.x+width,cluster.x)), ey = Math.max(placement.y,Math.min(placement.y+height,cluster.y));
          const distance = Math.hypot(ex-cluster.x,ey-cluster.y);
          element?.setAttribute("data-label-distance", String(distance));
          if (distance > 30) L.polyline([[group.lat,group.lon],instance!.containerPointToLatLng([ex,ey])], { interactive:false,color:color?.fill??"#d0c9be",weight:.8,opacity:.55 }).addTo(places);
        } else label.hidden = true;
        function select() { if (grouped) chooseCluster.current(cluster.groups.map(place => place.key)); else choose.current(group.key); }
        marker.on("click", select); activate(element, select);
        if (element) {
          const keys = cluster.groups.map(place => place.key); element.setAttribute("role","button"); element.setAttribute("aria-label", name.textContent === caption ? title : `${name.textContent}. ${title}`); element.setAttribute("aria-pressed",String(active)); element.dataset.placeKeys = keys.join("|");
          const recordKeys = [...new Set(entries.map(entry => `${entry.item.kind}:${entry.item.id}`))];
          markerElements.current.push({ element, keys, records: recordKeys });
          element.classList.toggle("is-hovered", keys.includes(hover.current.place) || recordKeys.includes(hover.current.record));
        }
      }
      // Background labels orient the reader; they never geocode a record.
      const orientationLimit = Math.max(3, Math.min(12, Math.floor(size.x * size.y / 85000)));
      let orientationLabels = 0;
      for (const feature of [...(geography.current?.features ?? [])].sort((a,b) => (a.properties?.rank ?? 9) - (b.properties?.rank ?? 9))) {
        if (orientationLabels >= orientationLimit) break;
        const p = feature.properties;
        const rankLimit = instance!.getZoom() < 3 ? 2 : instance!.getZoom() < 5 ? 3 : 5;
        if (!p || !Number.isFinite(p.lat) || !Number.isFinite(p.lon) || p.rank > rankLimit) continue;
        const point = instance!.latLngToContainerPoint([p.lat, p.lon]), width = Math.min(140, p.name.length * 7 + 10);
        const rect = { x: point.x - width / 2, y: point.y - 10, width, height: 20 };
        if (rect.x < 12 || rect.y < 16 || rect.x + width > size.x - 12 || rect.y > size.y - 38) continue;
        if (occupied.some(r => rect.x < r.x + r.width + 12 && rect.x + width > r.x - 12 && rect.y < r.y + r.height + 5 && rect.y + 20 > r.y - 5)) continue;
        const label = document.createElement("span"); label.textContent = p.name;
        const marker = L.marker([p.lat, p.lon], { interactive: false, keyboard: false, icon: L.divIcon({ className: "map-country-label", html: label, iconSize: [width, 20], iconAnchor: [width / 2, 10] }) }).addTo(labels);
        marker.getElement()?.setAttribute("aria-hidden", "true"); occupied.push(rect); orientationLabels++;
      }
      if (focused) markerElements.current.find(marker => marker.keys.includes(focused))?.element.focus({ preventScroll:true });
    }
    draw(); instance.on("moveend zoomend resize", draw);
    return () => { instance.off("moveend zoomend resize", draw); places.remove(); labels.remove(); markerElements.current = []; };
  }, [groups, selected, selectedRecord, ready, busy, colors, panOpen, detailsVisible]);

  useEffect(() => {
    if (!map.current || !ready || !geography.current || !highlightRegions || busy) return;
    const countries = eventCountryGroups(groups), frames = regionFrames.current;
    function eventRegion(code: string) {
      const group = countries.get(code)!;
      const entries = group.entries.filter(entry => entry.item.kind === "event" && entry.connection.countryCode === code);
      const active = entries.find(entry => `event:${entry.item.id}` === selectedRecord);
      const owner = active ?? entries[0], color = colors[mapIdentity(owner.item)]?.hex ?? "#625d55";
      return { group, entries, active, color, record: active ? `event:${active.item.id}` : entries.length === 1 ? `event:${owner.item.id}` : undefined };
    }
    function selectRegion(code: string) { const region = eventRegion(code); if (chooseEvent.current) chooseEvent.current(region.group.key, region.record); else choose.current(region.group.key); }
    const layer = L.geoJSON(geography.current, {
      filter: feature => countries.has(feature.properties?.code),
      style: feature => { const region = eventRegion(feature?.properties?.code); return { className: "map-event-region", color: region.color, weight: region.active ? 2.5 : 1.5, fillColor: region.color, fillOpacity: region.active ? 0.42 : 0.25 }; },
      onEachFeature: (feature, polygon) => {
        const group = countries.get(feature.properties?.code)!; frames.set(group.key, countryFocusBounds(feature, group));
        const region = eventRegion(feature.properties?.code);
        const label = document.createElement("span"); label.textContent = `${region.entries.map(entry => entry.item.title).slice(0,3).join(" / ")} · ${group.name} · modern country outline`;
        polygon.bindTooltip(label, { sticky: true }); polygon.on("click", () => selectRegion(feature.properties?.code));
      },
    }).addTo(map.current);
    layer.eachLayer(polygon => {
      const path = polygon as L.Path & { feature?: { properties?: { code?: string } } };
      const group = countries.get(path.feature?.properties?.code ?? ""), element = path.getElement();
      if (!group || !element) return;
      const code = path.feature?.properties?.code ?? "", region = eventRegion(code);
      element.setAttribute("tabindex", "0"); element.setAttribute("role", "button"); element.setAttribute("aria-label", `${region.entries.map(entry => entry.item.title).slice(0,3).join(" / ")}, ${group.name}, modern country outline`); element.setAttribute("aria-pressed", String(Boolean(region.active))); element.setAttribute("data-event-country", code); activate(element, () => selectRegion(code));
    });
    return () => { layer.remove(); frames.clear(); };
  }, [groups, selected, selectedRecord, colors, ready, highlightRegions, busy]);
  function reset(keys?: string[]) {
    if (busy || !map.current) return;
    const targets = keys ? groups.filter(group => keys.includes(group.key)) : groups;
    if (keys && !targets.length) return;
    map.current.invalidateSize({ pan: false });
    const bounds = L.latLngBounds(targets.map(group => [group.lat,group.lon] as [number,number]));
    for (const [key, frame] of regionFrames.current) if (!keys || keys.includes(key)) bounds.extend(frame);
    if (keys) for (const group of targets.filter(group => group.country)) {
      const code = group.entries.find(entry => entry.connection.countryCode)?.connection.countryCode;
      const feature = geography.current?.features.find(feature => feature.properties?.code === code);
      if (feature) bounds.extend(countryFocusBounds(feature, group));
    }
    const surface = host.current!.getBoundingClientRect(), panel = host.current!.closest(".map-workspace")?.querySelector<HTMLElement>(".map-place-panel:not([hidden])")?.getBoundingClientRect();
    const bottom = panel && panel.top > surface.top && panel.top < surface.bottom ? Math.min(surface.height - 90, surface.bottom - panel.top + 24) : 36;
    const maxZoom = keys ? targets.length > 1 ? 10 : Math.max(5, map.current.getZoom()) : 5;
    if (bounds.isValid()) map.current.fitBounds(bounds,{paddingTopLeft:[44,84],paddingBottomRight:[80,bottom],maxZoom,animate:false});
    else map.current.setView([25,10],2,{animate:false});
  }
  useEffect(() => {
    if (ready && !busy && groups.length && !framed.current) { reset(); framed.current=true; }
    // Only the first loaded selection frames automatically. Later changes keep the camera.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready,busy,groups]);
  useEffect(() => {
    if (!ready || busy || !focusRequest || handledFocus.current === focusRequest.revision || !groups.some(group => focusRequest.keys.includes(group.key))) return;
    reset(focusRequest.keys); handledFocus.current = focusRequest.revision; host.current?.focus({ preventScroll: true });
    // Requests are explicit camera actions; later visibility changes keep the camera.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusRequest, ready, busy, groups]);
  useEffect(() => {
    const group = groups.find(place => place.key === selected);
    if (!ready || busy || !focusSelection || !group || !map.current || inspected.current === selected) return;
    inspected.current = selected;
    const instance = map.current;
    instance.invalidateSize({ pan: false });
    const point = instance.latLngToContainerPoint([group.lat,group.lon]), size = instance.getSize();
    const surface = host.current!.getBoundingClientRect(), panel = host.current!.closest(".map-workspace")?.querySelector<HTMLElement>(".map-place-panel:not([hidden])")?.getBoundingClientRect();
    const bottom = panel && panel.top > surface.top && panel.top < surface.bottom ? panel.top - surface.top - 32 : size.y - 58;
    if (point.x < 30 || point.x > size.x - 80 || point.y < 84 || point.y > bottom) instance.panBy([point.x - (size.x - 50) / 2, point.y - (bottom + 84) / 2],{animate:false});
  }, [selected,ready,busy,focusSelection,groups]);
  const controlPaths = { plus:"M12 5v14M5 12h14", minus:"M5 12h14", fit:"M8 3H3v5m13-5h5v5M3 16v5h5m8 0h5v-5", move:"M12 3v18M3 12h18m-12-6 3-3 3 3M9 18l3 3 3-3M6 9l-3 3 3 3m12-6 3 3-3 3", north:"m6 14 6-6 6 6", south:"m6 10 6 6 6-6", west:"m14 6-6 6 6 6", east:"m10 6 6 6-6 6" };
  const icon = (name:keyof typeof controlPaths) => <svg viewBox="0 0 24 24" aria-hidden="true"><path d={controlPaths[name]}/></svg>;
  return <div className="catalogue-map-surface">
    <div ref={host} inert={busy} className="catalogue-map-geography" role="region" aria-label="Place map. Use arrow keys to pan, plus and minus to zoom. Places are also listed beside the map." />
    <div className="map-navigation-controls" role="group" aria-label="Map controls">
      <button type="button" aria-label="Zoom in" title="Zoom in" disabled={busy||!ready} onClick={()=>map.current?.zoomIn()}>{icon("plus")}</button>
      <button type="button" aria-label="Zoom out" title="Zoom out" disabled={busy||!ready} onClick={()=>map.current?.zoomOut()}>{icon("minus")}</button>
      <button type="button" aria-label="Fit visible places" title="Fit visible places" disabled={busy||!ready} onClick={()=>reset()}>{icon("fit")}</button>
      <button type="button" aria-label="Pan controls" title="Pan controls" aria-expanded={panOpen} disabled={busy||!ready} onClick={()=>setPanOpen(value=>!value)} onKeyDown={event=>{if(event.key==="Escape")setPanOpen(false);}}>{icon("move")}</button>
    </div>
    {panOpen&&<div className="map-direction-controls" role="group" aria-label="Move map" onKeyDown={event=>{if(event.key==="Escape"){event.stopPropagation();setPanOpen(false);host.current?.parentElement?.querySelector<HTMLButtonElement>('[aria-label="Pan controls"]')?.focus();}}}>
      {(["north","west","east","south"] as const).map(direction=><button key={direction} type="button" data-direction={direction} aria-label={`Move map ${direction}`} onClick={()=>{const offsets={north:[0,-160],south:[0,160],west:[-160,0],east:[160,0]};map.current?.panBy(offsets[direction] as [number,number],{animate:false});}}>{icon(direction)}</button>)}
    </div>}
    {!ready && <div className="map-surface-loading"><LoadingIndicator label="Loading the map…" /></div>}
    {error && <p className="map-surface-error" role="status">The background map could not load. Place details remain available. <button onClick={() => setRetry(v => v + 1)}>Retry map</button></p>}
  </div>;
}
