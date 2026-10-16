import { describe, expect, it } from "vitest";
import { clusterPlaces, artistMapRelations, eventCountryGroups, connectionYears, placeGroups, sourceHref, type LocatedItem } from "./map";
const entry = (precision: string, lat: number | null = 0): LocatedItem => ({ item: { id: "one", kind: "book", title: "A book" }, connection: { place: "A place", relation: "written in", precision, lat, lon: 0, start: null, end: null, note: "", sourceLabel: "" } });
describe("map evidence", () => {
 it("groups colocated connections without mixing country precision with city precision", () => { const groups = placeGroups([entry("city"), entry("city"), entry("country"), entry("unlocated", null)]); expect(groups).toHaveLength(2); expect(groups[0].entries).toHaveLength(2); expect(groups[1].country).toBe(true); });
 it("does not convert an unknown bound into a definite date", () => { expect(connectionYears(entry("city").connection)).toBe("Association dates unrecorded"); expect(connectionYears({ ...entry("city").connection, start: -500, end: null })).toBe("500 BCE–?"); });
 it("rejects executable source links", () => { expect(sourceHref("javascript:alert(1)")).toBeUndefined(); expect(sourceHref("https://museum.example/work")).toBe("https://museum.example/work"); });
});

describe("map relationship semantics", () => {
 it("preserves an explicitly empty artist selection across reloads", () => {
  expect(artistMapRelations(new URLSearchParams())).toContain("creation");
  expect(artistMapRelations(new URLSearchParams("map_relation=none"))).toEqual([]);
  expect(artistMapRelations(new URLSearchParams("map_relation=birth&map_relation=creation"))).toEqual(["creation", "birth"]);
 });
 it("shades only explicit event country locations, never a city or other catalogue kind", () => {
  const country = entry("country"); country.item.kind = "event"; country.connection.countryCode = "FR";
  const city = entry("city"); city.item.kind = "event"; city.connection.countryCode = "GB";
  const book = entry("country"); book.connection.countryCode = "US";
  const historical = entry("unlocated", null); historical.item.kind = "event";
  expect([...eventCountryGroups(placeGroups([country, city, book, historical])).keys()]).toEqual(["FR"]);
 });
});

describe("bounded map marker clustering", () => {
 it("groups nearby screen positions while preserving every distinct place", () => {
  const groups = placeGroups([entry("city"), { ...entry("city", 1), connection: { ...entry("city", 1).connection, place: "Second town" } }, entry("city", 10)]);
  const clusters = clusterPlaces(groups, g => ({ x: g.lat * 10, y: 0 }), 30);
  expect(clusters).toHaveLength(2);
  expect(clusters.flatMap(c => c.groups).map(g => g.key).sort()).toEqual(groups.map(g => g.key).sort());
  expect(clusters.find(c => c.groups.length === 2)?.groups.map(g => g.name)).toContain("Second town");
 });
 it("keeps the selected place visible and remains deterministic across response order", () => {
  const groups = placeGroups([entry("city"), entry("country"), entry("city", 1)]);
  const project = (g: typeof groups[number]) => ({ x: g.lat, y: 0 });
  const selected = groups[0].key;
  const clusters = clusterPlaces(groups, project, 72, selected);
  expect(clusters.find(c => c.groups.some(g => g.key === selected))?.groups).toHaveLength(1);
  expect(clusterPlaces([...groups].reverse(), project, 72, selected)).toEqual(clusters);
 });
});
