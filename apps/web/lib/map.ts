export type MapKind = "artist" | "artwork" | "book" | "event";
export type MapItem = { id: string; kind: MapKind; title: string; context?: string; years?: string; image?: string };
export type PlaceConnection = { place: string; relation: string; precision: string; lat: number | null; lon: number | null; start: number | null; end: number | null; note: string; sourceUrl?: string; sourceLabel: string };
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
