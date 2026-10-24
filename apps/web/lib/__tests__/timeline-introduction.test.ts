import { expect, it } from "vitest";
import { guideLanguages } from "../museum-guide-types";
import { timelineGuideContext, timelineIntroductionCopy } from "../timeline-introduction";

it("has complete, locally authored copy for every guide language", () => {
  expect(Object.keys(timelineIntroductionCopy).sort()).toEqual(Object.keys(guideLanguages).sort());
  for (const [locale, copy] of Object.entries(timelineIntroductionCopy)) {
    expect(Object.keys(copy)).toEqual(Object.keys(timelineIntroductionCopy.en));
    for (const value of Object.values(copy)) expect(value.trim().length).toBeGreaterThan(0);
    if (locale !== "en") expect(copy.artworks).not.toBe(timelineIntroductionCopy.en.artworks);
    expect(timelineGuideContext(new URLSearchParams({ guide: "mary-cassatt", guide_lang: locale }))).toEqual({ fromGuide: true, locale });
  }
});

it.each(["", "guide_lang=ar", "guide=../louvre&guide_lang=ar", "guide=%3Cscript%3E&guide_lang=ar"])("ignores invalid guide context: %s", query => {
  expect(timelineGuideContext(new URLSearchParams(query))).toEqual({ fromGuide: false, locale: "en" });
});

it.each(["", "xx", "constructor", "__proto__"])("falls back to English for an unsupported language: %s", language => {
  expect(timelineGuideContext(new URLSearchParams({ guide: "louvre", guide_lang: language }))).toEqual({ fromGuide: true, locale: "en" });
});
