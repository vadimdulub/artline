export type MapKind = "artist" | "artwork" | "book" | "event";
export type MapItem = { id: string; kind: MapKind; title: string; context?: string; years?: string; image?: string; colorKey?: string; slug?: string };
export type PlaceConnection = { key?: string; place: string; relation: string; categories?: string[]; countryCode?: string; precision: string; lat: number | null; lon: number | null; start: number | null; end: number | null; dateDisplay?: string; note: string; sourceUrl?: string; sourceLabel: string };
export type MapRecord = { id: string; connections: PlaceConnection[]; truncated: boolean };
export type LocatedItem = { item: MapItem; connection: PlaceConnection };
export type PlaceGroup = { key: string; lat: number; lon: number; country: boolean; precision: string; name: string; entries: LocatedItem[] };
export function placeGroups(entries: LocatedItem[]): PlaceGroup[] {
  const groups = new Map<string, PlaceGroup>();
  for (const entry of entries) {
    const c = entry.connection;
    if (c.lat === null || c.lon === null || !Number.isFinite(c.lat) || !Number.isFinite(c.lon) || Math.abs(c.lat) > 90 || Math.abs(c.lon) > 180) continue;
    const country = c.precision === "country";
    const key = `${c.lat},${c.lon},${country ? "country" : c.precision === "recorded point" ? "point" : "local"}`;
    const group = groups.get(key) ?? { key, lat: c.lat, lon: c.lon, country, precision: c.precision, name: c.place, entries: [] };
    group.entries.push(entry); groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => a.name.localeCompare(b.name));
}
export function connectionYears(c: PlaceConnection): string {
  if (c.dateDisplay?.trim()) return c.dateDisplay.trim();
  const year = (value: number) => value < 0 ? `${Math.abs(value)} BCE` : String(value);
  if (c.start === null && c.end === null) return "Association dates unrecorded";
  if (c.start === c.end) return year(c.start!);
  return `${c.start === null ? "?" : year(c.start)}–${c.end === null ? "?" : year(c.end)}`;
}
export function sourceHref(url?: string): string | undefined {
  if (!url) return;
  try { const parsed = new URL(url); if (["https:", "http:"].includes(parsed.protocol)) return parsed.href; } catch { /* no unsafe links */ }
}

export const artistPlaceFilters = [
  { value: "creation", label: "Paintings made" },
  { value: "birth", label: "Born" },
  { value: "residence", label: "Lived or worked" },
  { value: "education", label: "Studied" },
  { value: "death", label: "Died" },
  { value: "travel", label: "Travelled" },
  { value: "association", label: "Country affiliations" },
] as const;
export function artistMapRelations(params: URLSearchParams): string[] {
  if (!params.has("map_relation")) return artistPlaceFilters.filter(f => f.value !== "association").map(f => f.value);
  return artistPlaceFilters.filter(f => params.getAll("map_relation").includes(f.value)).map(f => f.value);
}
// Only an explicit country-level event location may shade a country polygon.
// A city point, an artist's nationality, or a book's origin cannot do so.
export function eventCountryGroups(groups: PlaceGroup[]): Map<string, PlaceGroup> {
  const countries = new Map<string, PlaceGroup>();
  for (const group of groups) for (const { item, connection } of group.entries) {
    if (item.kind === "event" && connection.precision === "country" && connection.countryCode) countries.set(connection.countryCode, group);
  }
  return countries;
}

export const mapKindNames: Record<MapKind, string> = { artist: "Artist", artwork: "Artwork", book: "Book", event: "Event" };
export const mapSymbolPaths: Record<MapKind, string[]> = {
  artist: ["M15 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0", "M5 20v-2a7 7 0 0 1 14 0v2"],
  artwork: ["M3 4h18v16H3z", "m3 16 5-5 4 4 3-3 6 5", "M16 8h.01"],
  book: ["M12 5v15", "M12 5C9 3 6 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1"],
  event: ["M5 21V3", "M5 4h14l-3 5 3 5H5"],
};
export function placeRecordCount(group: PlaceGroup): number {
  return new Set(group.entries.map(({ item }) => `${item.kind}:${item.id}`)).size;
}
export function placeKind(group: PlaceGroup): MapKind {
  return group.entries.find(e => e.item.image)?.item.kind ?? group.entries[0]?.item.kind ?? "artist";
}
export function relationLabel(value: string): string {
  const labels: Record<string, string> = { birth: "Born in", death: "Died in", studio: "Studio in", active: "Worked in", education: "Studied in", travel: "Travelled to", created: "Created in", begun: "Begun in", continued: "Continued in", completed: "Completed in", citizenship: "Citizenship", cultural_affiliation: "Cultural affiliation", historical_region: "Historical region" };
  return labels[value] ?? value.charAt(0).toUpperCase() + value.slice(1);
}
export function placeTopics(group: PlaceGroup): string {
  const names: Record<string, string> = { creation: "Artworks", birth: "Birth", residence: "Life & work", education: "Study", death: "Death", travel: "Travel", association: "Country links", writing: "Writing", publication: "Publication", event: "Events" };
  return [...new Set(group.entries.flatMap(e => e.connection.categories ?? []).map(c => names[c]).filter(Boolean))].join(" · ") || [...new Set(group.entries.map(e => mapKindNames[e.item.kind]))].join(" · ");
}

export type PlaceCluster = { x: number; y: number; groups: PlaceGroup[] };
// Display-only screen clustering of the current bounded page. The anchor is an
// existing place; selection prioritizes its anchor without introducing overlapping targets.
export function clusterPlaces(groups: PlaceGroup[], project: (group: PlaceGroup) => { x: number; y: number }, radius = 60, selected = ""): PlaceCluster[] {
  const cells = new Map<string, PlaceCluster[]>(), clusters: PlaceCluster[] = [];
  for (const group of [...groups].sort((a, b) => Number(b.key === selected) - Number(a.key === selected) || a.key.localeCompare(b.key))) {
    const { x, y } = project(group);
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    const cluster = { x, y, groups: [group] };
    const cx = Math.floor(x / radius), cy = Math.floor(y / radius);
    let found: PlaceCluster | undefined;
    for (let dx = -1; dx <= 1 && !found; dx++) for (let dy = -1; dy <= 1 && !found; dy++) {
      found = cells.get(`${cx + dx}:${cy + dy}`)?.find(c => Math.hypot(c.x - x, c.y - y) < radius);
    }
    if (found) found.groups.push(group);
    else { const key = `${cx}:${cy}`; cells.set(key, [...(cells.get(key) ?? []), cluster]); clusters.push(cluster); }
  }
  return clusters;
}

// Older API responses remain readable during a staged rollout. New responses
// supply stable evidence keys and chronological order from Go.
export function connectionKey(c: PlaceConnection): string {
  return c.key ?? JSON.stringify([c.place, c.relation, c.precision, c.lat, c.lon, c.start, c.end, c.sourceUrl ?? "", c.sourceLabel]);
}
export function connectionPlaceKey(c: PlaceConnection): string {
  if (c.lat === null || c.lon === null || !Number.isFinite(c.lat) || !Number.isFinite(c.lon) || Math.abs(c.lat) > 90 || Math.abs(c.lon) > 180) return "";
  return `${c.lat},${c.lon},${c.precision === "country" ? "country" : c.precision === "recorded point" ? "point" : "local"}`;
}

export function groupPlaceConnections(groups: PlaceGroup[]): { item: MapItem; connections: PlaceConnection[] }[] {
  const records = new Map<string, { item: MapItem; connections: PlaceConnection[] }>();
  for (const group of groups) for (const { item, connection } of group.entries) {
    const key = `${item.kind}:${item.id}`;
    if (!records.has(key)) records.set(key, { item, connections: [] });
    records.get(key)!.connections.push(connection);
  }
  for (const record of records.values()) record.connections.sort((a, b) => {
    const left = a.start ?? a.end, right = b.start ?? b.end;
    if (left !== null && right !== null) return left - right;
    if (left !== null) return -1;
    if (right !== null) return 1;
    return Number(Boolean(b.dateDisplay)) - Number(Boolean(a.dateDisplay));
  });
  return [...records.values()];
}
