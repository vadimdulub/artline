import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { BookSummary, BooksResponse } from "../lib/books";
import covers from "../../server/internal/books/cover-selection.json";

// Browser-only responses exercise exact boundaries without catalogue fixtures.
async function mockSelection(page: Page, total: number, undated = 0) {
  const requests: URLSearchParams[] = [];
  await page.route("**/api/backend/v1/books**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/facets")) return route.fulfill({ json: { languages: [], countries: [], regions: [] } });
    if (url.pathname.endsWith("/authors")) return route.fulfill({ json: { items: [], hasMore: false } });
    const params = url.searchParams;
    requests.push(params);
    const count = params.get("women") === "true" ? total : 301;
    const pageSize = Number(params.get("limit") ?? 150);
    const items: BookSummary[] = Array.from({ length: Math.min(count, pageSize) }, (_, i) => ({
      summary: true, id: `capacity-${i}`, title: `Book ${i + 1}`, author: "Woman author", years: i < count - undated ? "1900" : "Dates not established",
      startYear: i < count - undated ? 1900 : null, endYear: i < count - undated ? 1900 : null, approximate: false, cover: covers[0],
    }));
    const response: BooksResponse = {
      items, total: count, selectionTotal: 301, undatedTotal: undated,
      hasMore: count > pageSize, nextCursor: count > pageSize ? "next" : "",
      range: { start: -5000, end: 2000 }, bounds: { start: -5000, end: 2000 },
      mode: count <= 300 ? "individual" : "density", periods: [], ticks: [], density: [],
    };
    return route.fulfill({ json: response });
  });
  return requests;
}

for (const total of [200, 300]) for (const width of [1440, 390]) {
  test(`${total} women-authored books all appear on the timeline at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    const requests = await mockSelection(page, total, 2);
    await page.goto("/books?women=true&after=old-index-cursor");
    await expect(page.locator(".book-mark")).toHaveCount(total - 2);
    await expect(page.getByRole("list", { name: "Books without established dates" }).getByRole("button")).toHaveCount(2);
    await expect(page.locator(".library-card")).toHaveCount(0);
    await expect(page.locator(".books-gallery-guidance")).toHaveCount(0);
    expect(requests[0].get("top100")).toBe("false");
    expect(requests[0].get("limit")).toBe("300");
    expect(requests[0].has("after")).toBe(false);
    await page.locator(".book-mark").last().focus();
    await expect(page.locator(".book-mark").last()).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`books-${total}-${width}.png`) });
  });
}

for (const width of [1440, 1024, 768, 390, 320]) {
  test(`301 books show covers and filtering guidance at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await mockSelection(page, 301);
    await page.goto("/books?women=true");
    await expect(page.locator(".library-card")).toHaveCount(300);
    await expect(page.locator(".library-card img").first()).toBeVisible();
    await expect(page.locator(".books-gallery-guidance")).toContainText("301 books match. Add filters or narrow the years");
    await expect(page.locator(".book-mark")).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`books-covers-${width}.png`) });
    if (width === 320) {
      const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
      expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
    }
  });
}

test("choosing women authors replaces highlights and moves a complete matching selection onto the timeline", async ({ page }) => {
  const requests = await mockSelection(page, 300);
  await page.goto("/books");
  await expect(page.locator(".library-card")).toHaveCount(300);
  await page.getByRole("checkbox", { name: "Women authors", exact: true }).check();
  await expect(page.locator(".book-mark")).toHaveCount(300);
  await expect(page.getByRole("checkbox", { name: "Book highlights", exact: true })).not.toBeChecked();
  expect(requests.at(-1)?.get("top100")).toBe("false");
  await page.reload();
  await expect(page.locator(".book-mark")).toHaveCount(300);
  await page.goBack();
  await expect(page.locator(".library-card")).toHaveCount(300);
});

test("the real women-author selection uses the same bounded timeline rule and retains covers", async ({ page, request }) => {
  const response = await request.get("/api/backend/v1/books?women=true&top100=false&summary=true&start=1900&end=1950");
  expect(response.ok()).toBe(true);
  const data = await response.json() as BooksResponse;
  expect(data.total).toBeGreaterThan(150);
  expect(data.total).toBeLessThanOrEqual(300);
  expect(data.mode).toBe("individual");
  expect(data.items).toHaveLength(data.total);
  expect(data.hasMore).toBe(false);
  await page.goto("/books?women=true&start=1900&end=1950");
  await expect(page.locator(".book-mark")).toHaveCount(data.total);
  await page.getByRole("button", { name: "Zoom out" }).click();
  await expect(page.locator(".library-card")).toHaveCount(300);
  await expect(page.locator(".books-gallery-guidance")).toBeVisible();
  const cover = page.locator(".library-card img").first();
  await expect.poll(() => cover.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
});
