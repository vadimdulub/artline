import { describe, expect, it } from "vitest";
import { clusterPlaces, artistMapRelations, eventCountryGroups, connectionPlaceKey, connectionYears, groupPlaceConnections, placeGroups, sourceHref, type LocatedItem } from "./map";
const entry = (precision: string, lat: number | null = 0): LocatedItem => ({ item: { id: "one", kind: "book", title: "A book" }, connection: { place: "A place", relation: "written in", precision, lat, lon: 0, start: null, end: null, note: "", sourceLabel: "" } });
describe("map evidence", () => {
 it("groups colocated connections without mixing country precision with city precision", () => { const groups = placeGroups([entry("city"), entry("city"), entry("country"), entry("unlocated", null)]); expect(groups).toHaveLength(2); expect(groups[0].entries).toHaveLength(2); expect(groups[1].country).toBe(true); });
 it("holds invalid coordinates as unmapped rather than drawing impossible places", () => {
  expect(placeGroups([entry("city", 91), { ...entry("city"), connection: { ...entry("city").connection, lon: 181 } }, entry("city", 45)])).toHaveLength(1);
  expect(connectionPlaceKey(entry("city", 91).connection)).toBe("");
 });
 it("does not convert an unknown bound into a definite date", () => { expect(connectionYears(entry("city").connection)).toBe("Association dates unrecorded"); expect(connectionYears({ ...entry("city").connection, start: -500, end: null })).toBe("500 BCE–?"); });
 it("preserves the recorded date qualification", () => {
  expect(connectionYears({ ...entry("city").connection, start: 1500, end: 1500, dateDisplay: "c. 1500" })).toBe("c. 1500");
  expect(connectionYears({ ...entry("city").connection, dateDisplay: "1498–1502" })).toBe("1498–1502");
 });
 it("rejects executable source links", () => { expect(sourceHref("javascript:alert(1)")).toBeUndefined(); expect(sourceHref("https://museum.example/work")).toBe("https://museum.example/work"); });
});

describe("location record timelines", () => {
 it("groups the same record across places and orders dated milestones before undated evidence", () => {
  const unknown = entry("city");
  const dated = { ...entry("city", 1), connection: { ...entry("city", 1).connection, end: 1818 } };
  const earlier = { ...entry("city", 2), connection: { ...entry("city", 2).connection, start: 1816 } };
  const groups = placeGroups([unknown, dated, earlier]);
  const before = JSON.stringify(groups);
  const records = groupPlaceConnections(groups);
  expect(records).toHaveLength(1);
  expect(records[0].connections).toEqual([earlier.connection, dated.connection, unknown.connection]);
  expect(JSON.stringify(groups)).toBe(before);
 });
 it("keeps people with the same name distinct and retains a qualified date without numeric bounds", () => {
  const unknown = entry("city"), qualified = { ...entry("city"), connection: { ...entry("city").connection, dateDisplay: "early 1500s" } };
  const other = { ...entry("city"), item: { ...entry("city").item, id: "two" } };
  const records = groupPlaceConnections(placeGroups([unknown, qualified, other]));
  expect(records).toHaveLength(2);
  expect(records[0].connections).toEqual([qualified.connection, unknown.connection]);
  expect(records[0].connections[0].start).toBeNull();
 });
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
 it("keeps square hit areas separate even for diagonal places", () => {
  const groups = placeGroups(Array.from({ length: 30 }, (_, index) => entry("city", index)));
  const clusters = clusterPlaces(groups, group => ({ x: (group.lat % 6) * 39, y: Math.floor(group.lat / 6) * 39 }), 64);
  for (const [index, a] of clusters.entries()) for (const b of clusters.slice(index + 1)) expect(Math.abs(a.x - b.x) >= 44 || Math.abs(a.y - b.y) >= 44).toBe(true);
  expect(clusters.flatMap(cluster => cluster.groups)).toHaveLength(groups.length);
 });
 it("groups nearby screen positions while preserving every distinct place", () => {
  const groups = placeGroups([entry("city"), { ...entry("city", 1), connection: { ...entry("city", 1).connection, place: "Second town" } }, entry("city", 10)]);
  const clusters = clusterPlaces(groups, g => ({ x: g.lat * 10, y: 0 }), 30);
  expect(clusters).toHaveLength(2);
  expect(clusters.flatMap(c => c.groups).map(g => g.key).sort()).toEqual(groups.map(g => g.key).sort());
  expect(clusters.find(c => c.groups.length === 2)?.groups.map(g => g.name)).toContain("Second town");
 });
 it("anchors the selected place without overlapping nearby targets and remains deterministic", () => {
  const groups = placeGroups([entry("city"), entry("country"), entry("city", 1)]);
  const project = (g: typeof groups[number]) => ({ x: g.lat, y: 0 });
  const selected = groups[0].key;
  const clusters = clusterPlaces(groups, project, 72, selected);
  expect(clusters[0].groups[0].key).toBe(selected);
  expect(clusters[0].groups).toHaveLength(3);
  expect(clusterPlaces([...groups].reverse(), project, 72, selected)).toEqual(clusters);
 });
});
