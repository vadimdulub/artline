import type { MapItem, MapKind } from "./map";

export const mapLayers = [
  { kind: "artist", name: "Painters" },
  { kind: "artwork", name: "Artworks" },
  { kind: "book", name: "Books" },
  { kind: "event", name: "Events" },
] as const;

export function activeMapLayers(params: URLSearchParams): Set<MapKind> {
  const values = params.getAll("map_layer");
  if (values.includes("none")) return new Set();
  const selected = values.filter((value): value is MapKind => mapLayers.some(layer => layer.kind === value));
  return new Set(selected.length ? selected : mapLayers.map(layer => layer.kind));
}

export function mapLayerValue(layers: Set<MapKind>): string[] | null {
  const values = mapLayers.filter(layer => layers.has(layer.kind)).map(layer => layer.kind);
  return values.length === mapLayers.length ? null : values.length ? values : ["none"];
}

export function mapVisibility(params: URLSearchParams): (item: MapItem) => boolean {
  const layers = activeMapLayers(params), none = params.get("map_visibility") === "none";
  const hidden = new Set(params.getAll("map_hide")), shown = new Set(params.getAll("map_show"));
  return item => layers.has(item.kind) && (none ? shown.has(`${item.kind}:${item.id}`) : !hidden.has(`${item.kind}:${item.id}`));
}
