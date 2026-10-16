import { describe, expect, it } from "vitest";
import { connectionYears, placeGroups, sourceHref, type LocatedItem } from "./map";
const entry = (precision: string, lat: number | null = 0): LocatedItem => ({ item: { id: "one", kind: "book", title: "A book" }, connection: { place: "A place", relation: "written in", precision, lat, lon: 0, start: null, end: null, note: "", sourceLabel: "" } });
describe("map evidence", () => {
 it("groups colocated connections without mixing country precision with city precision", () => { const groups = placeGroups([entry("city"), entry("city"), entry("country"), entry("unlocated", null)]); expect(groups).toHaveLength(2); expect(groups[0].entries).toHaveLength(2); expect(groups[1].country).toBe(true); });
 it("does not convert an unknown bound into a definite date", () => { expect(connectionYears(entry("city").connection)).toBe("Association dates unrecorded"); expect(connectionYears({ ...entry("city").connection, start: -500, end: null })).toBe("500 BCE–?"); });
 it("rejects executable source links", () => { expect(sourceHref("javascript:alert(1)")).toBeUndefined(); expect(sourceHref("https://museum.example/work")).toBe("https://museum.example/work"); });
});
