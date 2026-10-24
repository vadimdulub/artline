"use client";
import dynamic from "next/dynamic";
import { useEffect, useId, useMemo, useRef, useState, useSyncExternalStore, type CSSProperties } from "react";
import { updateQuery, useQueryString } from "@/lib/url-state";
import { connectionKey, connectionPlaceKey, placeGroups, type MapItem, type MapKind, type MapRecord, type PlaceConnection } from "@/lib/map";
import { mapIdentity, mapIdentityColors } from "@/lib/map-colors";
import { activeMapLayers, mapLayers as kinds, mapLayerValue, mapVisibility } from "@/lib/map-layers";
import type { CatalogueMapProps } from "./CatalogueMap";
import { MapRecordJourney } from "./MapRecordJourney";
import { MapMenu } from "./MapMenu";
import { NavigationIcon } from "./MemberNavigation";
import { MapPlaceChoices } from "./MapPlaceChoices";
import { MapPickerContext, type ActiveMapPicker } from "./MapPickerFrame";
import { MapRecordPicker } from "./MapRecordPicker";
import { LoadingIndicator } from "./LoadingIndicator";
import "./CatalogueMap.css";
import "./MapWorkspace.css";
import "./MapAtlas.css";
import "./MapPickers.css";
const MapSurface = dynamic(() => import("./MapSurface"), { ssr: false, loading: () => <div className="map-loading"><LoadingIndicator label="Opening the map…" /></div> });

const itemKey = (item: MapItem) => `${item.kind}:${item.id}`;
const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
const compactQuery = "(max-width: 1199px)";
function subscribeCompact(callback: () => void) { const query = window.matchMedia(compactQuery); query.addEventListener?.("change", callback); return () => query.removeEventListener?.("change", callback); }
function compactSnapshot() { return window.matchMedia(compactQuery).matches; }
const serverSnapshot = () => false;
const layerIcons: Record<MapKind, string> = { artist: "artists", artwork: "artworks", book: "guide", event: "events" };
function Icon({ kind }: { kind: "layers" | "back" | "close" | "search" | "chevron" | "expand" }) {
  const paths = { back: "m14 6-6 6 6 6", layers: "m3 7 9-4 9 4-9 4-9-4Zm0 5 9 4 9-4M3 17l9 4 9-4", close: "m6 6 12 12M18 6 6 18", search: "M17 17l4 4M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0", chevron: "m7 10 5 5 5-5", expand: "M14 4h6v6m0-6-7 7M10 20H4v-6m0 6 7-7" };
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d={paths[kind]} /></svg>;
}
function GroupCheck({ checked, mixed, label, onChange, disabled }: { checked: boolean; mixed: boolean; label: string; onChange: (checked: boolean) => void; disabled: boolean }) {
  const ref = useRef<HTMLInputElement>(null);
  useEffect(() => { if (ref.current) ref.current.indeterminate = mixed; }, [mixed]);
  return <input ref={ref} type="checkbox" aria-label={label} checked={checked} disabled={disabled} onChange={event => onChange(event.target.checked)} />;
}

export function MapWorkspace({ items, total, onOpen, children, layerPicker, layerPickers, headingId, busy, failure, records, retryLocations }: CatalogueMapProps & {
  busy: boolean; failure?: string; records: Record<string, MapRecord>; retryLocations: () => void;
}) {
  const queryString = useQueryString(), params = new URLSearchParams(queryString), compact = useSyncExternalStore(subscribeCompact, compactSnapshot, serverSnapshot);
  const explicitRecord = params.get("map_record") ?? "", explicitStop = params.get("map_stop") ?? "";
  const placeKey = params.get("map_place") ?? "";
  const hidden = new Set(params.getAll("map_hide")), shown = new Set(params.getAll("map_show")), none = params.get("map_visibility") === "none";
  const layers = activeMapLayers(params), enabled = mapVisibility(params);
  const [hovered, setHovered] = useState(""), [previewRecord, setPreviewRecord] = useState("");
  const [layerView, setLayerView] = useState<"open" | "closed">("closed"), [detailsOpen, setDetailsOpen] = useState(true), [expanded, setExpanded] = useState(false);
  const [activePicker, setActivePicker] = useState<ActiveMapPicker>();
  const pickerLayer = kinds.find(layer => layer.name === activePicker?.name);
  const [focusRequest, setFocusRequest] = useState<{ keys: string[]; revision: number }>();
  const layersVisible = layerView === "open";
  const layersID = useId(), detailsID = useId();
  const layerButton = useRef<HTMLButtonElement>(null), choicesHeading = useRef<HTMLHeadingElement>(null);
  const detailsPanel = useRef<HTMLElement>(null);
  const colors = useMemo(() => mapIdentityColors(items), [items]);
  const colorStyle = (item: MapItem): CSSProperties => ({ "--map-identity": colors[mapIdentity(item)]?.hex, "--map-identity-fill": colors[mapIdentity(item)]?.fill } as CSSProperties);
  const entries = useMemo(() => items.flatMap(item => (records[itemKey(item)]?.connections ?? []).map(connection => ({ item, connection }))), [items, records]);
  const allGroups = useMemo(() => placeGroups(entries), [entries]);
  const located = new Set(allGroups.flatMap(group => group.entries.map(entry => itemKey(entry.item))));
  const groups = useMemo(() => {
    const visible = mapVisibility(new URLSearchParams(queryString));
    return placeGroups(entries.filter(entry => visible(entry.item)));
  }, [entries, queryString]);
  const storedPlaces = params.getAll("map_places"), locationKeys = storedPlaces.length ? storedPlaces : placeKey ? [placeKey] : [];
  const choiceKind = kinds.some(layer => layer.kind === params.get("map_choice_kind")) ? params.get("map_choice_kind") : null, showChoices = params.get("map_panel") === "places";
  const focusedItem = explicitRecord ? items.find(item => itemKey(item) === explicitRecord) : undefined;
  const focusedRecord = focusedItem ? records[itemKey(focusedItem)] ?? { id: focusedItem.id, connections: [], truncated: false } : undefined;
  const stop = explicitStop || (focusedRecord?.connections[0] ? connectionKey(focusedRecord.connections[0]) : "");
  const selectedConnection = focusedRecord?.connections.find(connection => connectionKey(connection) === stop);
  const selectedPlace = showChoices ? placeKey : explicitRecord ? selectedConnection && focusedItem && enabled(focusedItem) ? connectionPlaceKey(selectedConnection) : "" : placeKey;
  const choiceGroups = groups.filter(group => locationKeys.includes(group.key)).map(group => choiceKind ? { ...group, entries: group.entries.filter(entry => entry.item.kind === choiceKind) } : group).filter(group => group.entries.length > 0);
  const choices = choiceGroups.flatMap(group => group.entries);
  const choiceRecordCount = new Set(choices.map(entry => itemKey(entry.item))).size;
  const locationGroups = allGroups.filter(group => locationKeys.includes(group.key));
  const locationTitle = locationGroups.length === 1 ? locationGroups[0].name : locationGroups.length ? `${locationGroups.length} nearby places` : "Location";
  const detailsVisible = detailsOpen && (showChoices || !!explicitRecord) && !(compact && layersVisible);
  const hasEvents = items.some(item => item.kind === "event"), highlightRegions = params.get("map_regions") !== "off" && hasEvents && layers.has("event");
  const Heading = headingId ? "h1" : "h2";

  function visibility(selected: MapItem[], checked: boolean) {
    const next = new Set(none ? shown : hidden);
    for (const item of selected) if (none ? checked : !checked) next.add(itemKey(item)); else next.delete(itemKey(item));
    const nextLayers = new Set(layers); if (checked) selected.forEach(item => nextLayers.add(item.kind));
    updateQuery({ ...(none ? { map_show: [...next] } : { map_hide: [...next] }), map_layer: mapLayerValue(nextLayers) }, true);
  }
  function layerVisibility(kind: MapKind, checked: boolean) {
    const next = new Set(layers); if (checked) next.add(kind); else next.delete(kind);
    updateQuery({ map_layer: mapLayerValue(next) }, true);
  }
  function selectConnection(item: MapItem, connection: PlaceConnection, keepLocation = true) {
    setHovered(""); setPreviewRecord(""); setDetailsOpen(true);
    if (compact) setLayerView("closed");
    updateQuery({ map_record: itemKey(item), map_stop: connectionKey(connection), map_place: connectionPlaceKey(connection) || null, map_panel: "records", ...(!keepLocation ? { map_places: null, map_choice_kind: null } : showChoices && !storedPlaces.length ? { map_places: locationKeys } : {}) }, true);
  }
  function selectRecord(item: MapItem, query = "") {
    const connections = records[itemKey(item)]?.connections ?? [];
    const connection = (query ? connections.find(connection => normalize(connection.place).includes(query)) : undefined) ?? connections[0];
    if (connection) selectConnection(item, connection, false);
    else { setDetailsOpen(true); if (compact) setLayerView("closed"); updateQuery({ map_record: itemKey(item), map_stop: null, map_place: null, map_panel: "records", map_places: null, map_choice_kind: null }, true); }
  }
  function openLocation(keys: string[], kind?: MapKind) {
    if (!keys.length) return;
    activePicker?.close(); setActivePicker(undefined); setHovered(keys[0]); setPreviewRecord(""); setDetailsOpen(true); setExpanded(false);
    if (compact) setLayerView("closed");
    updateQuery({ map_place: keys[0], map_places: keys, map_choice_kind: kind ?? null, map_panel: "places", map_record: null, map_stop: null }, true);
  }
  function selectPlace(key: string) { if (groups.some(group => group.key === key)) openLocation([key]); }
  function selectCluster(keys: string[]) { openLocation(keys); }
  function selectEventRegion(key: string) { if (groups.some(group => group.key === key)) openLocation([key], "event"); }
  function openLayers() { activePicker?.close(); setActivePicker(undefined); setLayerView("open"); requestAnimationFrame(() => document.getElementById(layersID)?.querySelector<HTMLElement>("summary")?.focus({ preventScroll: true })); }
  function closeLayers() { activePicker?.close(); setActivePicker(undefined); setLayerView("closed"); requestAnimationFrame(() => layerButton.current?.focus({ preventScroll: true })); }
  function backFromPicker() { activePicker?.close(true); setActivePicker(undefined); }
  function backToLocation() { setDetailsOpen(true); setPreviewRecord(""); updateQuery({ map_panel: "places", map_place: locationKeys.includes(placeKey) ? placeKey : locationKeys[0] ?? null }, true); }
  function framePlaces(keys: string[]) { setExpanded(false); if (compact) setLayerView("closed"); setFocusRequest(previous => ({ keys, revision: (previous?.revision ?? 0) + 1 })); }
  function closeDetails() { setDetailsOpen(false); setExpanded(false); requestAnimationFrame(() => layerButton.current?.focus({ preventScroll: true })); }
  useEffect(() => { if (showChoices && detailsVisible) { detailsPanel.current?.querySelector(".map-details-body")?.scrollTo?.({ top: 0, behavior: "instant" }); choicesHeading.current?.focus({ preventScroll: true }); } }, [placeKey, showChoices, detailsVisible]);

  const detailActions = <><button className="map-icon-button map-expand-details" aria-label={expanded ? "Collapse information" : "Expand information"} aria-expanded={expanded} onClick={() => setExpanded(value => !value)}><Icon kind="expand" /></button><button className="map-icon-button" aria-label="Close details" onClick={closeDetails}><Icon kind="close" /></button></>;

  return <section className="catalogue-map map-workspace-v2" aria-label="Places connected with these results" aria-busy={busy}>
    <Heading id={headingId} tabIndex={headingId ? -1 : undefined} className="sr-only">Places connected with this selection</Heading>

    <div className="map-workspace" data-layers={layersVisible} data-details={detailsVisible} data-expanded={expanded}>
      {compact && layersVisible && <button className="map-layer-backdrop" aria-hidden="true" tabIndex={-1} onClick={closeLayers} />}
      <aside id={layersID} hidden={!layersVisible} className="map-layer-panel" data-picker-open={!!activePicker} aria-label="Map layers" onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); closeLayers(); } }}>
        <MapPickerContext.Provider value={setActivePicker}>
        <div className="map-panel-heading">
          {activePicker && <button className="map-icon-button map-picker-back" aria-label="Back to layers" onClick={backFromPicker}><Icon kind="back" /></button>}
          <h2>{activePicker?.name ?? "Layers"}</h2>
          {pickerLayer && <label className="map-picker-visibility" title={`Show ${pickerLayer.name.toLowerCase()}`}><GroupCheck checked={layers.has(pickerLayer.kind)} mixed={false} label={`Show ${pickerLayer.name.toLowerCase()}`} disabled={false} onChange={value => layerVisibility(pickerLayer.kind, value)} /></label>}
          <button className="map-icon-button" aria-label="Close layers" onClick={closeLayers}><Icon kind="close" /></button>
        </div>
        <div className="map-layer-scroll">
          <>
            {kinds.map(({ kind, name }) => {
              const members = items.filter(item => item.kind === kind), custom = layerPickers?.[kind];
              if (!members.length && !custom) return null;
              const active = layers.has(kind);
              return <section className="map-record-group map-layer-picker-row" hidden={!!activePicker && activePicker.name !== name} key={kind} data-layer={kind} data-enabled={active}>
                <label className="map-layer-control-check" hidden={!!activePicker}><GroupCheck checked={active} mixed={false} label={`Show ${name.toLowerCase()}`} disabled={false} onChange={value => layerVisibility(kind, value)} /></label>
                <span className="map-layer-kind-icon" hidden={!!activePicker}><NavigationIcon kind={layerIcons[kind]} /></span>
                {custom ?? <MapRecordPicker name={name} items={members} records={records} active={active} selected={explicitRecord} enabled={enabled} located={located} onVisibility={(item, value) => visibility([item], value)} onInspect={selectRecord} onPreview={setPreviewRecord} colorStyle={colorStyle} />}
              </section>;
            })}
            {layerPicker && <div className="map-layer-picker">{layerPicker}</div>}
            {failure ? <p className="map-panel-intro">Place details are temporarily unavailable.</p> : busy ? <div className="map-list-skeleton" aria-hidden="true">{[0, 1, 2, 3].map(key => <span key={key} />)}</div> : !items.length && <p className="map-panel-intro" role="status">No records match these filters.</p>}
          </>
        </div>
        </MapPickerContext.Provider>
      </aside>
      <div className="map-canvas-wrap" inert={compact && (layersVisible || (detailsVisible && expanded))}>
    <div className="map-workspace-toolbar">
      <button ref={layerButton} className="map-layer-toggle" aria-label="Layers" title="Layers" aria-controls={layersID} aria-expanded={layersVisible} onClick={() => layersVisible ? closeLayers() : openLayers()}><Icon kind="layers" /></button>
    </div>
        <MapSurface busy={busy} focusRequest={focusRequest} detailsVisible={detailsVisible} highlightRegions={highlightRegions} groups={groups} selected={selectedPlace} hovered={hovered} previewRecord={previewRecord} selectedRecord={explicitRecord} onSelect={selectPlace} onEventSelect={selectEventRegion} onCluster={selectCluster} colors={colors} focusSelection={!!explicitRecord || !!placeKey} />
        {failure && <div className="map-feedback" role="alert"><strong>Places couldn’t load</strong><p>Try again to show locations for these records.</p><button onClick={retryLocations}>Try again</button></div>}
        {!busy && !failure && !groups.length && <div className="map-feedback" role="status">
          <strong>{!items.length ? "No records in this selection" : !items.some(enabled) ? "Nothing shown" : "No mapped places in this selection"}</strong>
          <p>{!items.length ? "Choose other years or adjust the catalogue filters." : !items.some(enabled) ? "Turn on a layer to explore its places." : "Records with unknown locations are available in the list."}</p>
          {!items.length ? <button onClick={() => { const toggle = document.querySelector<HTMLButtonElement>(".explorer .atlas-filter-toggle"); if (toggle?.getAttribute("aria-expanded") === "false") toggle.click(); toggle?.focus(); }}>Change filters</button> : <button onClick={openLayers}>{!items.some(enabled) ? "Choose layers" : "View records"}</button>}
        </div>}
        <MapMenu className="map-guide" label="Map notes"><div>
          <p className="map-coverage">{failure ? "Place evidence unavailable" : busy ? "Finding documented places…" : `${located.size} of ${items.length} loaded records located · ${total.toLocaleString("en-GB")} matching records`}</p>
          <p>City and area markers are approximate. Country markers identify a whole country. Modern outlines provide orientation.</p>
          <p>Dates and sources describe documented connections, not a complete travel route.</p>
          {Object.values(records).some(record => record.truncated) && <p>Some records have more evidence. Up to 32 matching connections per record are shown.</p>}
        </div></MapMenu>
      </div>
      <aside ref={detailsPanel} id={detailsID} hidden={!detailsVisible} className="map-place-panel" aria-label="Map details" style={!showChoices && focusedItem ? colorStyle(focusedItem) : undefined} onKeyDown={event => { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); closeDetails(); } }}>
        {showChoices ? <><div className="map-panel-heading map-location-heading"><h2 ref={choicesHeading} tabIndex={-1}>{locationTitle}</h2><div className="map-location-actions">{detailActions}</div></div><p className="map-location-count" role="status">{busy ? "Loading connections…" : failure ? "Connections unavailable" : `${choiceRecordCount} ${choiceRecordCount === 1 ? "record" : "records"}`}</p></> : (!focusedItem || !focusedRecord || busy || failure) && <div className="map-panel-heading map-details-heading">{detailActions}</div>}
        <div className={`map-details-body${showChoices ? " map-location-body" : ""}`}>
          {showChoices ? failure ? <p className="map-panel-intro">Place evidence is temporarily unavailable.</p> : busy ? <LoadingIndicator label="Finding documented places…" /> : choices.length ? <MapPlaceChoices groups={choiceGroups} onSelect={selectConnection} onZoom={() => framePlaces(choiceGroups.map(group => group.key))} onPreview={setPreviewRecord} colorStyle={colorStyle} selectedRecord={explicitRecord} selectedStop={stop} /> : <p className="map-panel-intro">No visible connections at this location. Turn on a layer to see its records.</p> : failure ? <p className="map-panel-intro">Place evidence is temporarily unavailable.</p> : busy ? <LoadingIndicator label="Finding documented places…" /> : focusedItem && focusedRecord ? <>
            {storedPlaces.length > 0 && <button className="map-record-back" onClick={backToLocation}><Icon kind="back" />Back to location</button>}
            {!enabled(focusedItem) && <p className="map-hidden-status">Hidden on map <button onClick={() => visibility([focusedItem], true)}>Show on map</button></p>}
            <MapRecordJourney item={focusedItem} record={focusedRecord} selected={stop} headingLevel={headingId ? 2 : 3} onSelect={connection => selectConnection(focusedItem, connection)} onLocate={enabled(focusedItem) && groups.some(group => group.key === selectedPlace) ? () => framePlaces([selectedPlace]) : undefined} onOpen={onOpen} actions={detailActions} autoFocus={!!explicitRecord || !!explicitStop} />
            {focusedItem.kind === "event" && <fieldset className="map-event-layer-controls"><legend>Events layer</legend><label><input type="checkbox" aria-label="Show events layer" checked={layers.has("event")} onChange={event => layerVisibility("event", event.target.checked)} /><span>Show events</span></label><label><input type="checkbox" aria-label="Colour event countries" checked={params.get("map_regions") !== "off"} disabled={!layers.has("event")} onChange={event => updateQuery({ map_regions: event.target.checked ? null : "off" }, true)} /><span>Colour recorded countries</span></label></fieldset>}
          </> : <p className="map-panel-intro">{explicitRecord ? "This record is not on the current page. Choose another record from the map." : "Choose a name or place to see its details."}</p>}
        </div>
      </aside>
    </div>

    {children}
  </section>;
}
