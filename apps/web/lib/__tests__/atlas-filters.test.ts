import { describe, expect, it } from "vitest";
import { allAtlasKinds, atlasLayers, layersAfterFilter, readEntityFilters } from "../atlas-filters";

describe("All filter discovery", () => {
  for (const query of ["country=japan", "country=japan&country=france", "continent=asia", "region=eastern-asia", "q=Monet", "preset=edo", "start=1600&end=1900", "highlights=true"]) {
    it(`opens all layers from a shared ${query} filter`, () => {
      expect(atlasLayers(new URLSearchParams(query))).toEqual(allAtlasKinds);
    });
  }
  for (const query of ["", "panel=add", "q=", "q=%20", "selection=true&country=japan", "selection=true&preset=edo", "selection=true&pick_book=legacy"]) {
    it(`keeps an unselected or explicitly empty canvas: ${query}`, () => {
      expect(atlasLayers(new URLSearchParams(query))).toEqual([]);
    });
  }
  it("retains explicit layer choices instead of restoring removed layers", () => {
    const params = new URLSearchParams("type=book&type=event&country=japan");
    expect(atlasLayers(params)).toEqual(["book", "event"]);
    expect(layersAfterFilter(atlasLayers(params), { country: ["japan", "france"] })).toEqual(["book", "event"]);
  });
  for (const updates of [{ country: ["japan"] }, { continent: ["asia"] }, { region: "eastern-asia" }, { q: "Monet" }, { highlights: "true" }] as Record<string, string | string[] | null>[]) {
    it(`populates an empty canvas when applying ${Object.keys(updates)[0]}`, () => {
      expect(layersAfterFilter([], updates)).toEqual(allAtlasKinds);
    });
  }
  for (const updates of [{ country: [] }, { continent: [] }, { region: null }, { q: " " }] as Record<string, string | string[] | null>[]) {
    it(`does not load all history when clearing ${Object.keys(updates)[0]} on an empty canvas`, () => {
      expect(layersAfterFilter([], updates)).toEqual([]);
    });
  }
});

describe("Add retains the current discovery scope", () => {
  for (const type of allAtlasKinds) {
    const top = type === "artwork" ? "popular" : "top100";
    for (const query of ["highlights=false", "country=japan&highlights=false"]) {
      it(`${type}: does not silently restrict all matches to Top 100 (${query})`, () => {
        expect(readEntityFilters(type, new URLSearchParams(query)).get(top)).toBe("false");
      });
    }
    it(`${type}: enables highlights by default without limiting artwork creators`, () => {
      expect(readEntityFilters(type, new URLSearchParams()).get(top)).toBe(type === "artwork" ? "false" : "true");
    });
    it(`${type}: honors explicit highlights and native overrides`, () => {
      expect(readEntityFilters(type, new URLSearchParams("highlights=true")).get(top)).toBe(type === "artwork" ? "false" : "true");
      expect(readEntityFilters(type, new URLSearchParams(`highlights=false&${type}_${top}=true`)).get(top)).toBe("true");
      expect(readEntityFilters(type, new URLSearchParams(`highlights=true&${type}_${top}=false`)).get(top)).toBe("false");
    });
  }
  it("keeps repeated native filters without copying global or other-layer filters", () => {
    const filters = readEntityFilters("book", new URLSearchParams("country=japan&book_language=Q5287&book_language=Q150&event_topic=Conflict"));
    expect(filters.getAll("language")).toEqual(["Q5287", "Q150"]);
    expect(filters.has("country")).toBe(false);
    expect(filters.has("topic")).toBe(false);
  });
});
