import { describe, expect, it } from "vitest";
import { resolvedStartingFilters, startingFilters } from "../atlas-starting-points";
import type { AtlasPreset } from "../atlas";
import presets from "../../../server/internal/atlas/presets.json";
const period = (id: string) => presets.find(p => p.id === id) as AtlasPreset;

describe("reviewed period selections", () => {
  it("resolves every shared starting point consistently with an explicit selection", () => {
    for (const p of presets as AtlasPreset[]) {
      const params = resolvedStartingFilters(new URLSearchParams({ preset: p.id }), p);
      expect(params.getAll("country")).toEqual(p.startingCountries ?? []);
      expect(params.getAll("creator")).toEqual(p.startingCreators ?? []);
      expect(params.get("highlights")).toBe(String(p.startingHighlights));
      expect(startingFilters(p).creator).toEqual(p.startingCreators ?? null);
    }
  });
  it("replaces movement creators and Highlights when choosing a broad period", () => {
    expect(startingFilters(period("civil-rights"))).toMatchObject({country:["united states"],highlights:"false"});
    expect(period("civil-rights").startingCreators?.filter(value => value.startsWith("painter:"))).toHaveLength(23);
    expect(startingFilters(period("renaissance"))).toMatchObject({creator:null,highlights:"true",continent:null,region:null});
    expect(startingFilters(period("french-revolution")).country).toEqual(["france"]);
  });
  it("preserves explicit shared-link filters and does not mutate the input", () => {
    const params = new URLSearchParams("creator=painter:test&country=cyprus&highlights=true");
    const before = params.toString();
    const result = resolvedStartingFilters(params, period("civil-rights"));
    expect(result.toString()).toBe(before);
    expect(params.toString()).toBe(before);
    expect(result.has("country_scope")).toBe(false);
  });
  it("retains intentionally empty selections across reloads and avoids native-facet conflicts", () => {
    const custom = new URLSearchParams("preset=civil-rights&preset_filters=custom&highlights=false");
    expect(resolvedStartingFilters(custom, period("civil-rights")).toString()).toBe(custom.toString());
    for (const query of ["artwork_painter=monet", "book_author=Homer"]) expect(resolvedStartingFilters(new URLSearchParams(query), period("civil-rights")).getAll("creator")).toEqual([]);
    for (const query of ["continent=asia", "region=western-asia", "artwork_country=CY", "artwork_region=western-asia"]) expect(resolvedStartingFilters(new URLSearchParams(query), period("civil-rights")).getAll("country")).toEqual([]);
  });
  it("leaves filters alone when zooming out", () => {
    expect(startingFilters(undefined)).toEqual({});
  });
});
