export type MapKind = "artist" | "artwork" | "book" | "event";
export type MapItem = { id: string; kind: MapKind; title: string; context?: string; years?: string; image?: string };
export type PlaceConnection = { place: string; relation: string; categories?: string[]; countryCode?: string; precision: string; lat: number | null; lon: number | null; start: number | null; end: number | null; note: string; sourceUrl?: string; sourceLabel: string };
export type MapRecord = { id: string; connections: PlaceConnection[]; truncated: boolean };
export type LocatedItem = { item: MapItem; connection: PlaceConnection };
export type PlaceGroup = { key: string; lat: number; lon: number; country: boolean; precision: string; name: string; entries: LocatedItem[] };
export function placeGroups(entries: LocatedItem[]): PlaceGroup[] {
  const groups = new Map<string, PlaceGroup>();
  for (const entry of entries) {
    const c = entry.connection;
    if (c.lat === null || c.lon === null || !Number.isFinite(c.lat) || !Number.isFinite(c.lon)) continue;
    const country = c.precision === "country";
    const key = `${c.lat},${c.lon},${country ? "country" : c.precision === "recorded point" ? "point" : "local"}`;
    const group = groups.get(key) ?? { key, lat: c.lat, lon: c.lon, country, precision: c.precision, name: c.place, entries: [] };
    group.entries.push(entry); groups.set(key, group);
  }
  return [...groups.values()].sort((a, b) => a.name.localeCompare(b.name));
}
export function connectionYears(c: PlaceConnection): string {
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
