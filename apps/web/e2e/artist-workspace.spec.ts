import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistDetail, ArtistWorksPage } from "../lib/types";

test("artist directory filters the real catalogue and keeps pages bounded", async ({ page }) => {
  await page.goto("/artists");
  await expect(page.getByRole("heading", { name: "Artists", exact: true })).toBeVisible();
  await expect(page.locator("main li h3")).toHaveCount(24);
  await page.getByRole("searchbox", { name: "Artist name" }).fill("Rembrandt");
  await page.getByRole("combobox", { name: "Country", exact: true }).selectOption("NL");
  await page.getByRole("button", { name: "Find artists", exact: true }).click();
  await expect(page).toHaveURL(/q=Rembrandt/);
  await expect(page.locator("main").getByRole("link", { name: /^Rembrandt van Rijn 1606/ })).toBeVisible();
  await expect(page.locator("main li h3")).not.toHaveCount(24);
  await page.getByRole("searchbox", { name: "Artist name" }).fill("ArtlineNonexistentArtistName");
  await page.getByRole("button", { name: "Find artists", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No artists match these filters" })).toBeVisible();
  await page.getByRole("link", { name: "Show all artists", exact: true }).click();
  const first = await page.locator("main li h3").allTextContents();
  await page.getByRole("link", { name: "Next artists", exact: true }).click();
  await expect(page).toHaveURL(/cursor=/);
  await expect(page.locator("main li h3")).toHaveCount(24);
  const second = await page.locator("main li h3").allTextContents();
  expect(second.some(name => first.includes(name))).toBe(false);
  await page.getByRole("link", { name: "First artists", exact: true }).click();
  await page.getByLabel("Top 1,000 cohort").check();
  await page.getByRole("button", { name: "Find artists", exact: true }).click();
  await expect(page.getByRole("heading", { name: "1,000 artists", exact: true })).toBeVisible();
});

for (const width of [1440, 390, 320]) {
  test(`one artist workspace exposes full works, biography and museums at ${width}px`, async ({ page }, info) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: 1000 });
    const artist = await (await page.request.get("/api/backend/v1/artists/rembrandt")).json() as ArtistDetail;
    expect(artist.artwork_count).toBeGreaterThan(1000);
    await page.goto("/artists/rembrandt?catalogue=all");
    await expect(page.getByRole("heading", { name: artist.display_name, exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Biography", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Wikipedia contributors", exact: true })).toBeVisible();
    const works = page.locator(".selected-works");
    await expect(works.locator(".work-card")).toHaveCount(24);
    await expect(works.getByRole("status")).toHaveText(`${artist.artwork_count!.toLocaleString("en-GB")} recorded works`);
    await page.screenshot({ path: info.outputPath(`artist-${width}.png`), fullPage: false });
    await works.getByRole("combobox", { name: "Work type", exact: true }).selectOption("painting");
    await expect(page).toHaveURL(/art_type=painting/);
    const filtered = await (await page.request.get("/api/backend/v1/artists/rembrandt/works?image_only=false&work_type=painting")).json() as ArtistWorksPage;
    await expect(works.locator(".work-title").first()).toHaveText(filtered.items[0].title);
    await works.getByRole("button", { name: "Next artworks", exact: true }).click();
    await expect(page).toHaveURL(/art_cursor=/);
    await expect(works.locator(".work-title").first()).not.toHaveText(filtered.items[0].title);
    await works.getByRole("button", { name: "Clear artwork filters" }).click();
    await expect(works.getByRole("combobox", { name: "Work type", exact: true })).toHaveValue("");
    const collection = page.getByRole("region", { name: "Museum holdings" });
    await expect(collection.locator("li")).toHaveCount(artist.collections!.length);
    await collection.getByRole("button", { name: "Browse works", exact: true }).first().click();
    await expect(works.getByRole("combobox", { name: "Museum / collection", exact: true })).toHaveValue(artist.collections![0].slug);
    await expect(works).toContainText(`${artist.collections![0].work_count.toLocaleString("en-GB")} matching works`);
    await works.locator(".work-card").first().click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(viewer).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  });
}

test("Van Gogh uses the same catalogue and title search preserves biography", async ({ page }) => {
  await page.goto("/artists/vincent-van-gogh-q5582?catalogue=all");
  await expect(page.locator(".artist-heading h1")).toHaveText("Vincent van Gogh");
  await expect(page.locator(".selected-works .work-card")).toHaveCount(24);
  await page.getByRole("searchbox", { name: "Search artworks", exact: true }).fill("ArtlineNonexistentCatalogueTitle");
  await page.getByRole("button", { name: "Search works", exact: true }).click();
  await expect(page.getByRole("heading", { name: "No matching artworks" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Biography", exact: true })).toBeVisible();
  await page.locator(".selected-works").getByRole("button", { name: "Clear artwork filters" }).first().click();
  await expect(page.locator(".selected-works .work-card")).toHaveCount(24);
});


test("full catalogue links preserve published-page visibility and work without JavaScript", async ({ page, browser, request }) => {
  const response = await request.get("/api/backend/v1/artists/rembrandt/works?preview=1&limit=1");
  const catalogue = await response.json() as ArtistWorksPage;
  const first = catalogue.items[0];
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const plain = await context.newPage();
    await plain.goto(`${test.info().project.use.baseURL}/artists/rembrandt/works/${first.id}?catalogue=all`);
    await expect(plain.getByRole("heading", { level: 1 })).toHaveText(first.title);
    await expect(plain.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
    await expect(plain.locator(".artwork-details h3")).toHaveText(first.title);
  } finally { await context.close(); }
  const publishedResponse = await request.get("/api/backend/v1/artists/rembrandt?preview=0");
  if (publishedResponse.status() === 404) return; // Local catalogue remains in review.
  expect(publishedResponse.ok()).toBe(true);
  const published = await publishedResponse.json() as ArtistDetail;
  await page.goto("/artists/rembrandt");
  await expect(page.locator(".selected-works").getByRole("status")).toHaveText(`${published.artwork_count!.toLocaleString("en-GB")} recorded works`);
  await page.getByRole("link", { name: "Browse the full recorded catalogue", exact: true }).click();
  await expect(page).toHaveURL(/catalogue=all/);
  await expect(page.locator(".selected-works .work-card")).toHaveCount(24);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
});
