import { expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { cleanEditorialBiography, referenceParagraphs } from "./biography";

const normalize = (text: string) => text.replace(/\s+/g, "");
it("preserves every word across all 1,000 reference biographies", () => {
  const records = JSON.parse(readFileSync("../server/internal/catalog/biographies.json", "utf8")) as Record<string, { text: string }>;
  expect(Object.keys(records)).toHaveLength(1000);
  for (const { text } of Object.values(records)) expect(normalize(referenceParagraphs(text).join(" "))).toBe(normalize(text));
  for (const slug of ["rembrandt", "claude-monet", "vincent-van-gogh-q5582"]) expect(referenceParagraphs(records[slug].text).length).toBeGreaterThan(2);
});
it("honours source paragraph breaks and keeps short paragraphs intact", () => {
  expect(referenceParagraphs("First paragraph.\nSecond paragraph.\n\nThird paragraph.")).toEqual(["First paragraph.", "Second paragraph.", "Third paragraph."]);
});
it("omits only known editorial workflow boilerplate, preserving the source and historical text", () => {
  const text = "Dutch painter.\n\nSource: [Wikidata](https://www.wikidata.org/wiki/Q5582) (CC0). Short authority description; full biography awaits editorial review.";
  expect(cleanEditorialBiography(text)).toBe("Dutch painter.\n\nSource: [Wikidata](https://www.wikidata.org/wiki/Q5582) (CC0).");
  expect(cleanEditorialBiography("His work was still in progress when he died.")).toBe("His work was still in progress when he died.");
});
