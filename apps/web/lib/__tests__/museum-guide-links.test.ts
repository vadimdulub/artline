import { describe, expect, it } from "vitest";
import institutions from "@/content/articles/museum-guides/institution-links.json";
import { getGuideIndex, getMuseumGuide } from "../museum-guides";
import { getGuideMuseumLinks, getMuseumGuideLinks, museumCollectionLabels } from "../museum-guide-links";
import { guideLanguages } from "../museum-guide-types";

describe("museum and guide cross-links", () => {
  it("connects every published museum guide to the same canonical museums in both directions", () => {
    const index = getGuideIndex();
    for (const [slug, museums] of Object.entries(institutions)) {
      const guide = index.find(entry => entry.slug === slug)!;
      expect(guide).toBeDefined();
      expect(guide.kind).not.toBe("artist");
      for (const locale of guide.locales) {
        const links = getGuideMuseumLinks(getMuseumGuide(slug, locale)!);
        expect(links.map(link => link.slug)).toEqual(museums);
        for (const link of links) {
          expect(link.href).toBe(`/museums/${link.slug}`);
          expect(link.name).toBeTruthy();
          expect(getMuseumGuideLinks(link.slug).map(entry => entry.slug)).toContain(slug);
        }
      }
    }
    expect(index.filter(guide => guide.kind !== "artist").map(guide => guide.slug).sort()).toEqual(Object.keys(institutions).sort());
  });

  it("keeps all three Munich museums and distinct guide/catalogue slugs", () => {
    expect(getGuideMuseumLinks(getMuseumGuide("munich-museums")!).map(link => link.name)).toEqual(["Alte Pinakothek", "Neue Pinakothek", "Lenbachhaus"]);
    expect(getGuideMuseumLinks(getMuseumGuide("louvre")!)[0].href).toBe("/museums/musee-du-louvre");
    expect(getMuseumGuideLinks("the-met").map(guide => guide.slug)).toEqual(["metropolitan-museum"]);
  });

  it("omits links for absent guides and artist guides and labels all ten editions", () => {
    expect(getMuseumGuideLinks("museum-without-guide")).toEqual([]);
    expect(getGuideMuseumLinks({ slug: "louvre", museum: "Louvre", kind: "artist" })).toEqual([]);
    for (const guide of getGuideIndex().filter(guide => guide.kind === "artist")) expect(getGuideMuseumLinks(guide)).toEqual([]);
    expect(Object.keys(museumCollectionLabels).sort()).toEqual(Object.keys(guideLanguages).sort());
    expect(Object.values(museumCollectionLabels).every(Boolean)).toBe(true);
  });
});
