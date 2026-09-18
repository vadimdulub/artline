import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { booksFixture, mockBooks } from "./books-fixture";

test("large Books overview compresses early years, keeps recent periods wide, and drills into periods", async ({ page }, testInfo) => {
  await mockBooks(page);
  await page.route("**/api/backend/v1/books?**", async route => {
    const url = new URL(route.request().url());
    if (url.searchParams.has("start") || url.searchParams.has("q")) return route.fallback();
    return route.fulfill({ json: {
      items: booksFixture, total: 10000, selectionTotal: 10000, hasMore: true, nextCursor: "next", range: { start: -5000, end: 2000 }, bounds: { start: -5000, end: 2000 },
      undatedTotal: 100, mode: "density",
      periods: [{ start: -5000, end: 2000, label: "Full range" }, { start: -5000, end: -1, label: "BCE" }],
      ticks: [{ year: -2500, label: "BCE" }, ...Array.from({ length: 20 }, (_, i) => ({ year: (i + 1) * 100, label: String((i + 1) * 100) }))],
      density: [{ start_year: -5000, end_year: -1, count: 300 }, ...Array.from({ length: 41 }, (_, i) => ({ start_year: i ? i * 50 : 1, end_year: i === 40 ? 2000 : i * 50 + 49, count: i < 20 ? 10 + i : 100 + i * 30 }))],
    } });
  });
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books?top100=false");
    const chart = page.getByRole("group", { name: "Explore books by period" });
    await expect(chart).toBeVisible();
    await expect(page.locator(".timeline-counter")).toContainText("10,000 books");
    await expect(page.locator("h1")).not.toContainText(/\bCE\b/);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440) {
      const first = await chart.getByRole("button").first().boundingBox();
      expect(first!.width / (await chart.boundingBox())!.width).toBeCloseTo(.05, 2);
      const modern = chart.getByRole("button", { name: /^Explore 1700–1749,/ });
      expect((await modern.boundingBox())!.x - (await chart.boundingBox())!.x).toBeCloseTo((await chart.boundingBox())!.width * .25, 0);
      // The compressed early columns still have visible bars.
      const earlyBar = chart.getByRole("button", { name: /^Explore 1000–1049,/ }).locator(".period-bar");
      expect((await earlyBar.boundingBox())!.width).toBeGreaterThan(1);
      expect((await page.locator(".timeline-dark").boundingBox())!.height).toBeGreaterThan(650);
    }
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations.map(v => v.id)).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`books-overview-${width}.png`) });
    const bce = chart.getByRole("button", { name: "Explore BCE, 300 books", exact: true });
    await bce.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByLabel("Book start year")).toHaveValue("-5000");
    await expect(page.getByLabel("Book end year")).toHaveValue("-1");
    await expect(page.locator(".book-mark")).toHaveCount(5);
    await page.goto("/books?top100=false");
    await chart.getByRole("button", { name: /^Explore 1900–1949,/ }).click();
    await expect(page.getByLabel("Book start year")).toHaveValue("1900");
    await expect(page.getByLabel("Book end year")).toHaveValue("1949");
    await expect(page.locator(".book-mark")).toHaveCount(4);
  }
});
