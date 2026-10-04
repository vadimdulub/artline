import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { BooksResponse } from "../lib/books";

for (const width of [1440, 390, 320]) test(`small book selections retain their timeline at ${width}`, async ({ page, request }, info) => {
  await page.setViewportSize({ width, height: 950 });
  const query = "top100=false&author=Jane%20Austen&limit=150";
  const result = await (await request.get(`/api/backend/v1/books?${query}`)).json() as BooksResponse;
  expect(result.mode).toBe("individual");
  expect(result.total).toBeLessThanOrEqual(150);
  await page.goto(`/books?${query}`);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const dated = result.items.filter(book => book.startYear !== null && book.endYear !== null);
  await expect(page.locator(".book-mark")).toHaveCount(dated.length);
  await expect(page.locator(".books-undated button")).toHaveCount(result.items.length - dated.length);
  await expect(page.locator(".library-strip")).toHaveCount(0);
  const mark = page.locator(".book-mark").first();
  await expect(mark.locator(":scope > span")).toHaveText(dated[0].title);
  await expect(mark.locator(".marker-context")).toHaveText(dated[0].years);
  await mark.focus(); await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog", { name: "Book details", exact: true })).toBeVisible();
  await page.keyboard.press("Escape"); await expect(mark).toBeFocused();
  if (result.undatedTotal) {
    await page.locator(".books-undated button").first().click();
    await expect(page.getByRole("dialog", { name: "Book details", exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`books-timeline-${width}.png`) });
});
