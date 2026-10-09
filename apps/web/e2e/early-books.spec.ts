import { expect, test } from "@playwright/test";
import selection from "../../../ops/curated-early-books-20260923.json";
import type { BooksResponse } from "../lib/books";

// Actual local catalogue, read-only: no fixtures and no mocked source records.
test("the reviewed early-book selection is highlighted with sourced dates", async ({ request }) => {
  const response = await request.get("/api/backend/v1/books?start=1&end=1600&top100=true&limit=200");
  expect(response.ok()).toBe(true);
  const data = await response.json() as BooksResponse;
  expect(data.hasMore).toBe(false);
  expect(data.items).toHaveLength(data.total);
  expect(data.total).toBeGreaterThanOrEqual(72);
  const books = new Map(data.items.map(book => [book.id, book]));
  for (const chosen of selection.items) {
    const book = books.get(`wd-${chosen.qid.toLowerCase()}`);
    expect(book, chosen.qid).toBeDefined();
    expect(book!.startYear).toBeGreaterThanOrEqual(1);
    expect(book!.endYear).toBeLessThanOrEqual(1600);
    expect(!book!.summary && book!.status).toBe("review");
    expect(!book!.summary && book!.sourceUrl).toBe(`https://www.wikidata.org/wiki/${chosen.qid}`);
  }
  expect(books.get("wd-q7317855")!.years).toContain("14th");
  expect(books.get("wd-q7317855")!.endYear).toBe(1500);
  expect(books.get("wd-q781898")!.startYear).toBe(1572);
  expect(books.get("wd-q19569020")!.author).toBe("Domentijan");
  const publicDetail = await request.get("http://127.0.0.1:8080/api/v1/books/wd-q1216330");
  expect(publicDetail.status()).toBe(200);
  expect((await publicDetail.json()).status).toBe("review");
});

for (const width of [1440, 390]) {
  test(`early-book highlights and source details display at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    const data = await (await page.request.get("/api/backend/v1/books?start=1&end=1600&top100=true")).json() as BooksResponse;
    await page.goto("/books?start=1&end=1600&top100=true");
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.locator(".timeline-counter")).toContainText(`${data.total} books`);
    await expect(page.getByRole("list", { name: "Book index", exact: true }).locator("li")).toHaveCount(data.total);
    await expect(page.locator(".book-mark")).toHaveCount(data.total);
    if (width < 760) await page.getByRole("button", { name: "Filters", exact: true }).click();
    await expect(page.getByRole("checkbox", { name: "Book highlights", exact: true })).toBeChecked();
    if (width < 760) await page.getByRole("button", { name: "Close filters", exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`early-books-${width}.png`) });
    await page.getByRole("button", { name: "Open Christian Topography by Cosmas Indicopleustes", exact: true }).click();
    const drawer = page.getByRole("dialog", { name: "Book details", exact: true });
    await expect(drawer.getByRole("heading", { name: "Christian Topography", exact: true })).toBeVisible();
    await expect(drawer).toContainText("c. 550");
    await expect(drawer.getByRole("link", { name: "Book source" })).toHaveAttribute("href", "https://www.wikidata.org/wiki/Q1216330");
    await expect(drawer.getByRole("link", { name: "CC BY-SA 4.0", exact: true })).toHaveAttribute("href", "https://creativecommons.org/licenses/by-sa/4.0/");
    const box = (await drawer.boundingBox())!;
    expect(await drawer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(box.width + 1);
    await page.screenshot({ path: info.outputPath(`early-book-details-${width}.png`) });
    await drawer.getByRole("button", { name: "Next book", exact: true }).click();
    await expect(drawer.getByRole("heading", { name: "Christian Topography", exact: true })).toHaveCount(0);
  });
}
