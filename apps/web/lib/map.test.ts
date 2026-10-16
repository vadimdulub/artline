import { describe, expect, it } from "vitest";
import { artistMapRelations, eventCountryGroups, connectionYears, placeGroups, sourceHref, type LocatedItem } from "./map";
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
