import "server-only";
import fs from "node:fs";
import path from "node:path";
import { cache } from "react";
import { guideLanguages, type GuideLocale, type GuideSummary, type MuseumGuide } from "./museum-guide-types";
const root = path.join(process.cwd(), "content", "articles");
const guideRoot = (entry: GuideSummary) => path.join(root, entry.kind === "artist" ? "artist-guides" : "museum-guides");
export const getGuideIndex = cache((): GuideSummary[] => ["artist-guides", "museum-guides"].flatMap(folder => JSON.parse(fs.readFileSync(path.join(root, folder, "index.json"), "utf8"))));
export const getMuseumGuide = cache((slug: string, locale: string = "en"): MuseumGuide | null => {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || !Object.hasOwn(guideLanguages, locale)) return null;
  const entry = getGuideIndex().find(guide => guide.slug === slug && guide.locales.includes(locale as GuideLocale));
  if (!entry) return null;
  return JSON.parse(fs.readFileSync(path.join(guideRoot(entry), slug, `${locale}.json`), "utf8"));
});
export function guidePDFPath(slug: string, locale: string): string | null {
  const entry = getGuideIndex().find(guide => guide.slug === slug);
  return entry && getMuseumGuide(slug, locale) ? path.join(guideRoot(entry), slug, `${locale}.pdf`) : null;
}
