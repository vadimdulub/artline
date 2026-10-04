import { expect, test } from "@playwright/test";
import type { BooksResponse } from "../lib/books";

for (const width of [1440, 390]) test(`books switch from covers to dates as years narrow at ${width}`, async ({ page, request }) => {
  await page.setViewportSize({ width, height: 950 });
  await page.goto("/books?top100=false&start=1800&end=1900");
  await expect(page.locator(".library-card")).toHaveCount(150);
  await page.getByLabel("Book start year", { exact: true }).fill("1811");
  await page.getByLabel("Book end year", { exact: true }).fill("1812");
  await page.getByLabel("Book end year", { exact: true }).press("Enter");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const narrow = await (await request.get("/api/backend/v1/books?top100=false&start=1811&end=1812&limit=150")).json() as BooksResponse;
  expect(narrow.mode).toBe("individual");
  await expect(page.locator(".book-mark")).toHaveCount(narrow.items.length);
  await expect(page.locator(".library-card")).toHaveCount(0);
  await page.getByRole("button", { name: "Zoom out to all years" }).click();
  await expect(page.locator(".library-card")).toHaveCount(150);
  expect(new URL(page.url()).searchParams.get("top100")).toBe("false");
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
});
