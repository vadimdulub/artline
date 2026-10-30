import { expect, it } from "vitest";
import institutions from "@/content/articles/museum-guides/institution-links.json";
import { museumDirectoryGuides } from "../museum-guide-directory";
import { getMuseumGuideLinks } from "../museum-guide-links";
import { guidePath } from "../museum-guide-types";

it("keeps directory guide destinations consistent with the museum page for every linked museum", () => {
  for (const museum of new Set(Object.values(institutions).flat())) {
    const expected = getMuseumGuideLinks(museum);
    const actual = museumDirectoryGuides(museum);
    expect(actual.map(guide => guide.href)).toEqual(expected.map(guide => guidePath(guide.slug)));
    expect(actual.map(guide => guide.title)).toEqual(expected.map(guide => guide.title));
    expect(actual.every(guide => guide.count > 0 && guide.languages > 0)).toBe(true);
  }
  expect(museumDirectoryGuides("museum-without-a-guide")).toEqual([]);
});
