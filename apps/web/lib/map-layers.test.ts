import { describe, expect, it } from "vitest";
import { activeMapLayers, mapLayerValue, mapVisibility } from "./map-layers";
import type { MapItem } from "./map";
const event: MapItem = { id: "revolution", kind: "event", title: "Revolution" };
const book: MapItem = { id: "book", kind: "book", title: "Book" };
describe("map layers", () => {
  it("starts with every layer enabled", () => expect([...activeMapLayers(new URLSearchParams())]).toEqual(["artist", "artwork", "book", "event"]));
  it("hides a whole kind, including records loaded on later pages", () => {
    const visible = mapVisibility(new URLSearchParams("map_layer=artist&map_layer=artwork&map_layer=book"));
    expect(visible(event)).toBe(false); expect(visible({ ...event, id: "next-page" })).toBe(false); expect(visible(book)).toBe(true);
  });
  it("retains individual record choices independently of layer visibility", () => {
    const params = new URLSearchParams("map_layer=event&map_hide=event:revolution");
    expect(mapVisibility(params)(event)).toBe(false); params.delete("map_layer");
    expect(mapVisibility(params)(event)).toBe(false); expect(mapVisibility(params)(book)).toBe(true);
  });
  it("stores an explicitly empty layer selection", () => {
    expect(mapLayerValue(new Set())).toEqual(["none"]); expect(mapVisibility(new URLSearchParams("map_layer=none"))(event)).toBe(false);
  });
  it("keeps old record-only visibility links readable", () => {
    const visible = mapVisibility(new URLSearchParams("map_visibility=none&map_show=book:book"));
    expect(visible(book)).toBe(true); expect(visible(event)).toBe(false);
  });
  it("serializes layers in a stable order and omits the default", () => {
    expect(mapLayerValue(new Set(["event", "artist"]))).toEqual(["artist", "event"]);
    expect(mapLayerValue(new Set(["artist", "artwork", "book", "event"]))).toBeNull();
  });
  it("ignores unsupported shared layer names", () => expect(activeMapLayers(new URLSearchParams("map_layer=invalid")).size).toBe(4));
});
