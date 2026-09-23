import { describe, expect, it } from "vitest";
import { startingGeography } from "../atlas-starting-points";
import type { AtlasPreset } from "../atlas";
import presets from "../../../server/internal/atlas/presets.json";
const period = (id: string) => presets.find(p => p.id === id) as AtlasPreset;

describe("period geography transitions", () => {
  it("applies every starting point from its metadata", () => {
    for (const p of presets as AtlasPreset[]) {
      expect(startingGeography(p, undefined, new URLSearchParams(), true)).toEqual({ country: p.startingCountries ?? null, country_scope: p.startingCountries?.length ? "artwork" : null, continent: null, region: null });
    }
  });
  it("replaces the previous period defaults when selecting another period", () => {
    const current = period("second-world-war"), next = period("renaissance");
    const params = new URLSearchParams({ country_scope: "artwork" });
    current.startingCountries!.slice().reverse().forEach(value => params.append("country", value));
    expect(startingGeography(next, current, params, false).country).toEqual(next.startingCountries);
    expect(startingGeography(period("byzantium"), current, params, false).country).toBeNull();
  });
  it("preserves custom countries, continents and regions from the dropdown", () => {
    for (const query of ["country=cyprus", "country=france&country_scope=artwork", "continent=asia", "region=western-asia"]) expect(startingGeography(period("renaissance"), period("second-world-war"), new URLSearchParams(query), false)).toEqual({});
  });
  it("preserves country filters on zoom out", () => {
    expect(startingGeography(undefined, period("second-world-war"), new URLSearchParams("country=france&country_scope=artwork"), false)).toEqual({});
  });
});
