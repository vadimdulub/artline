import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { BooksResponse } from "../lib/books";

// Read-only UI/API checks against the real researched catalogue.
async function count(page: import("@playwright/test").Page, value: number) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(`${value.toLocaleString("en-GB")} books`);
}

async function catalogueCounts(request: import("@playwright/test").APIRequestContext) {
  const [all, highlights, women, womenHighlights] = await Promise.all(
    ["top100=false", "top100=true", "women=true&top100=false", "women=true&top100=true"].map(async query => {
      const response = await request.get(`/api/backend/v1/books?${query}`);
      expect(response.ok()).toBe(true);
      return await response.json() as BooksResponse;
    }),
  );
  return { all, highlights, women, womenHighlights };
}

test("BCE books below the 150-object limit all appear as individual marks", async ({ page, request }) => {
  const response = await request.get("/api/backend/v1/books?top100=false&start=-5000&end=-1");
  expect(response.ok()).toBe(true);
  const books = await response.json() as BooksResponse;
  expect(books.total).toBeGreaterThan(100);
  expect(books.total).toBeLessThanOrEqual(150);
  expect(books.mode).toBe("individual");
  expect(books.items).toHaveLength(books.total);
  expect(books.hasMore).toBe(false);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/books?top100=false&start=-5000&end=-1");
    await count(page, books.total);
    await expect(page.locator(".book-mark")).toHaveCount(books.total);
    await expect(page.locator(".period-chart")).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

test("book highlights use bounded pages and retain complete navigation", async ({ page }, info) => {
  const response = await page.request.get("/api/backend/v1/books?top100=true");
  expect(response.ok()).toBe(true);
  const highlights = await response.json() as BooksResponse;
  expect(highlights.total).toBeGreaterThan(100);
  expect(highlights.items).toHaveLength(Math.min(highlights.total, 150));
  expect(highlights.items.length).toBeLessThanOrEqual(150);
  expect(highlights.mode).toBe("individual");
  expect(highlights.hasMore).toBe(highlights.total > 150);
  const authors = await (await page.request.get("/api/backend/v1/books?top100=true&view=authors")).json() as BooksResponse;
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/books"); await count(page, highlights.total);
    await expect(page.locator(".book-mark")).toHaveCount(highlights.items.filter(book => book.startYear !== null).length);
    await expect(page.locator(".period-chart")).toHaveCount(0);
    await expect(page.getByRole("list", { name: "Book index", exact: true }).locator("li")).toHaveCount(highlights.items.length);
    if (highlights.hasMore) {
      const next = await (await page.request.get(`/api/backend/v1/books?top100=true&after=${encodeURIComponent(highlights.nextCursor)}`)).json() as BooksResponse;
      await page.getByRole("button", { name: "Next books", exact: true }).click();
      await expect(page.getByRole("list", { name: "Book index", exact: true }).locator("li")).toHaveCount(next.items.length);
      await expect(page.getByRole("list", { name: "Book index", exact: true }).locator("li").first()).toContainText(next.items[0].title);
    } else await expect(page.getByRole("button", { name: "Next books", exact: true })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`all-book-highlights-${width}.png`) });
    await page.getByRole("list", { name: "Book index", exact: true }).locator("li").last().getByRole("button").click();
    await expect(page.getByRole("dialog", { name: "Book details", exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await page.getByRole("checkbox", { name: "Show author lifespans", exact: true }).check();
    await expect(page.locator(".book-author-mark")).toHaveCount(authors.authors!.filter(author => author.startYear !== null).length);
    await expect(page.locator(".period-chart")).toHaveCount(0);
  }
});

test("book discovery checkboxes combine, restore history and reset", async ({ page, request }) => {
  const totals = await catalogueCounts(request);
  await page.goto("/books");
  await count(page, totals.highlights.total);
  const women = page.getByRole("checkbox", { name: "Women authors", exact: true });
  const top = page.getByRole("checkbox", { name: "Book highlights", exact: true });
  await expect(women).not.toBeChecked();
  await expect(top).toBeChecked();
  await top.uncheck();
  await count(page, totals.all.total);
  await expect(page).toHaveURL(/top100=false/);
  await page.reload();
  await count(page, totals.all.total);
  await expect(top).not.toBeChecked();
  await page.goBack();
  await count(page, totals.highlights.total);
  await expect(top).toBeChecked();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(totals.highlights.items.length);
  await women.check();
  await count(page, totals.womenHighlights.total);
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(totals.womenHighlights.items.length);
  await page.reload();
  await count(page, totals.womenHighlights.total);
  await expect(women).toBeChecked();
  await expect(top).toBeChecked();
  await page.goBack();
  await count(page, totals.highlights.total);
  await expect(women).not.toBeChecked();
  await women.check();
  await count(page, totals.womenHighlights.total);
  await page.getByRole("button", { name: "Remove Book highlights filter", exact: true }).click();
  await count(page, totals.women.total);
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await count(page, totals.highlights.total);
  await expect(women).not.toBeChecked();
  await expect(top).toBeChecked();
  await expect(page.getByLabel("Find a book or author")).toBeFocused();
});

test("languages, regions and countries intersect with women and the Top 100", async ({ page, request }, testInfo) => {
  const totals = await catalogueCounts(request);
  await page.goto("/books?women=true&top100=true");
  await count(page, totals.womenHighlights.total);
  for (const [filter, name] of [["Languages", "French"], ["Regions", "Western Europe"], ["Countries", "France"]]) {
    await page.locator(`summary[aria-label^="${filter}:"]`).click();
    await page.getByRole("checkbox", { name, exact: true }).check();
    await page.getByRole("button", { name: "Done", exact: true }).click();
  }
  await count(page, 1);
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Open The Second Sex by Simone de Beauvoir", exact: true })).toBeVisible();
  const params = new URL(page.url()).searchParams;
  expect(params.get("language")).toBe("Q150");
  expect(params.get("region")).toBe("western-europe");
  expect(params.get("country")).toBe("Q142");
  await page.reload();
  await count(page, 1);
  await expect(page.locator('summary[aria-label="Languages: French"]')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("books-combined-filters.png") });
  await page.locator('summary[aria-label^="Countries:"]').click();
  await page.getByRole("checkbox", { name: "France", exact: true }).uncheck();
  await page.getByRole("checkbox", { name: "Japan", exact: true }).check();
  await page.keyboard.press("Escape");
  await count(page, 0);
  await expect(page.getByText(/No books match/)).toBeVisible();
  await page.getByRole("button", { name: "Clear filters", exact: true }).first().click();
  await count(page, totals.all.total);
});

test("shared filter bar fits small screens, accessible tooltip and retries facets", async ({ page, request }, testInfo) => {
  const totals = await catalogueCounts(request);
  let fail = true;
  await page.route("**/api/backend/v1/books/facets?**", route => fail ? route.fulfill({ status: 503, json: { error: { message: "Temporary test outage" } } }) : route.continue());
  await page.goto("/books");
  await count(page, totals.highlights.total);
  await expect(page.getByText("Some filter choices could not be loaded.")).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "Retry filters", exact: true }).click();
  await expect(page.getByText("Some filter choices could not be loaded.")).toHaveCount(0);
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books?top100=true");
    await count(page, totals.highlights.total);
    if (width <= 760) await page.getByRole("button", { name: "Filters", exact: true }).click();
    expect(await page.locator(".atlas-filter-row > .multi-filter summary > span:first-child").allTextContents()).toEqual(["Authors", "Regions", "Countries", "Languages"]);
    await page.getByRole("button", { name: "About the book highlights", exact: true }).focus();
    await expect(page.getByRole("tooltip")).toContainText("editorial");
    const tip = (await page.getByRole("tooltip").boundingBox())!;
    expect(tip.x).toBeGreaterThanOrEqual(0);
    expect(tip.x + tip.width).toBeLessThanOrEqual(width);
    await page.keyboard.press("Escape");
    await expect(page.getByRole("tooltip")).toHaveCount(0);
    if (width <= 760) await page.getByRole("button", { name: "Close filters", exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440) expect((await page.locator(".timeline-dark").boundingBox())!.height).toBeGreaterThan(650);
    await page.getByLabel("Book start year").hover();
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations.map(v => v.id)).toEqual([]);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: testInfo.outputPath(`books-filters-${width}.png`) });
  }
});
