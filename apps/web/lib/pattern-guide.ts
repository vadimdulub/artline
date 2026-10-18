import "server-only";
import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import type EnglishCopy from "@/content/articles/interactive-guides/islamic-patterns/en.json";
import assetData from "@/content/articles/interactive-guides/islamic-patterns/assets.json";
import { guideLanguages } from "./museum-guide-types";
import { absoluteURL, pageMetadata } from "./seo";

export type PatternGuideCopy = typeof EnglishCopy;
export type PatternInteractiveCopy = Pick<PatternGuideCopy, "ui" | "construction" | "symmetry" | "colour" | "studio">;
export const patternAssets = assetData;
export const patternGuidePath = (locale: string = "en") => `/guides/islamic-patterns${locale === "en" ? "" : `/${locale}`}`;
export function getPatternGuide(locale: string = "en"): PatternGuideCopy | undefined {
  if (!Object.hasOwn(guideLanguages, locale)) return;
  return JSON.parse(fs.readFileSync(path.join(process.cwd(), "content/articles/interactive-guides/islamic-patterns", `${locale}.json`), "utf8"));
}
export function patternGuideMetadata(copy: PatternGuideCopy): Metadata {
  const canonical = patternGuidePath(copy.locale);
  return {
    ...pageMetadata(`${copy.guideTitle}: ${copy.title}`, copy.intro, canonical, { image: patternAssets[0].variants[1].url }),
    alternates: {
      canonical: absoluteURL(canonical),
      languages: { ...Object.fromEntries(Object.keys(guideLanguages).map(locale => [locale, absoluteURL(patternGuidePath(locale))])), "x-default": absoluteURL(patternGuidePath()) },
    },
    openGraph: { type: "article", title: copy.guideTitle, description: copy.intro, url: absoluteURL(canonical), images: [{ url: absoluteURL(patternAssets[0].variants[1].url), alt: copy.hero.title }], locale: copy.locale === "en" ? "en_GB" : copy.locale },
  };
}
