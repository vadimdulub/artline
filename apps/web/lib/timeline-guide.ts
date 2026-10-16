import "server-only";
import fs from "node:fs";
import path from "node:path";
import { cache } from "react";
import { guideLanguages, type GuideLocale } from "./museum-guide-types";

export type TimelineGuide = {
  slug: "art-history-timeline";
  locale: GuideLocale;
  title: string;
  subtitle: string;
  introduction: string[];
  sections: { title: string; paragraphs: string[] }[];
  updated: string;
};

const root = path.join(process.cwd(), "content", "articles", "timeline-guide");

export const getTimelineGuide = cache((locale: string = "en"): TimelineGuide | null => {
  if (!Object.hasOwn(guideLanguages, locale)) return null;
  return JSON.parse(fs.readFileSync(path.join(root, `${locale}.json`), "utf8"));
});

export const timelineGuidePath = (locale: GuideLocale = "en") => `/art-history-timeline${locale === "en" ? "" : `/${locale}`}`;
