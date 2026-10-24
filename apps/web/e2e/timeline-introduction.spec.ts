import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mockMobileExplorers } from "./mobile-explorer-fixture";
import { timelineIntroductionCopy } from "../lib/timeline-introduction";
import { guidePortalLinks, type GuideLocale } from "../lib/museum-guide-types";

const links = guidePortalLinks({ slug: "louvre", locale: "en", context: { start: 1300, end: 1650 }, works: [] });
// Use the fixture’s exact object; no DB writes or remote service dependencies.
const selectedWork = "4a399ca8-712b-40db-8493-6d89b653773e";
const artworksURL = `${links.all}&artwork_id=${selectedWork}`;
const lifespansURL = `${links.painters}&painter=leonardo-da-vinci`;

test.beforeEach(async ({ page }) => {
  await page.route("**/*", route => new URL(route.request().url()).hostname === "localhost" || new URL(route.request().url()).hostname === "127.0.0.1" ? route.continue() : route.abort());
  await mockMobileExplorers(page);
});

test("first visit, keyboard dismissal, remembered state, reopening and independent lifespan help", async ({ page }) => {
  await page.goto(artworksURL);
  const note = page.locator('[data-timeline-introduction="artworks"]');
  await expect(note).toHaveAttribute("open");
  await expect(note).toContainText("selected books and historical events");
  await expect(page.locator(".all-lane")).toHaveCount(3);
  await note.getByRole("button", { name: "Got it" }).focus();
  await page.keyboard.press("Enter");
  await expect(note).not.toHaveAttribute("open");
  await expect(note.locator("summary")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(note).toHaveAttribute("open");
  await page.keyboard.press("Space");
  await expect(note).not.toHaveAttribute("open");
  await page.reload();
  await expect(note).not.toHaveAttribute("open");
  await page.goto(artworksURL.replace("guide=louvre", "guide=mary-cassatt"));
  await expect(note).not.toHaveAttribute("open");
  await page.goto(lifespansURL);
  const lives = page.locator('[data-timeline-introduction="lifespans"]');
  await expect(lives).toHaveAttribute("open");
  await expect(lives).toContainText("recorded lifespan or active years");
  await expect(lives).toContainText("artists linked from your guide");
  await lives.getByRole("button", { name: "Got it" }).click();
  await page.reload();
  await expect(lives).not.toHaveAttribute("open");
  await page.goto("/?view=paintings");
  await expect(lives).toHaveCount(0);
  await page.goto("/all?selection=true&type=artwork");
  await expect(note).toHaveCount(0);
});

for (const locale of Object.keys(timelineIntroductionCopy) as GuideLocale[]) {
  test(`${locale}: both notes are translated, accessible and fit desktop and mobile`, async ({ page }, info) => {
    const copy = timelineIntroductionCopy[locale];
    for (const [kind, url, title] of [["artworks", artworksURL, copy.artworksTitle], ["lifespans", lifespansURL, copy.lifespansTitle]] as const) {
      await page.goto(url.replace("guide_lang=en", `guide_lang=${locale}`));
      const note = page.locator(`[data-timeline-introduction="${kind}"]`);
      await expect(note).toHaveAttribute("open");
      await expect(note.locator("summary")).toContainText(title);
      await expect(note.locator("..")).toHaveAttribute("lang", locale);
      await expect(note.locator("..")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
      for (const width of [1440, 1024, 768, 390, 320]) {
        await page.setViewportSize({ width, height: 1000 });
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
        const box = await note.boundingBox();
        expect(box!.width).toBeLessThanOrEqual(width);
        expect(await note.getByRole("button").evaluate(el => el.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
        if (["en", "ru", "ar"].includes(locale)) {
          await note.scrollIntoViewIfNeeded();
          await page.screenshot({ path: info.outputPath(`${kind}-${width}.png`) });
        }
      }
      expect((await new AxeBuilder({ page }).include(`[data-timeline-introduction="${kind}"]`).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    }
  });
}

test("a guide note still works when local storage is blocked", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(Storage.prototype, "getItem", { value: () => { throw new DOMException("Blocked", "SecurityError"); } });
    Object.defineProperty(Storage.prototype, "setItem", { value: () => { throw new DOMException("Blocked", "SecurityError"); } });
  });
  await page.goto(artworksURL);
  const note = page.locator('[data-timeline-introduction="artworks"]');
  await expect(note).toHaveAttribute("open");
  await note.getByRole("button", { name: "Got it" }).click();
  await expect(note).not.toHaveAttribute("open");
  await note.locator("summary").click();
  await expect(note).toHaveAttribute("open");
});
