import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistDetail, ArtistWorksPage } from "../lib/types";

test("artist directory filters the real catalogue and keeps pages bounded", async ({ page }) => {
  await page.goto("/artists");
  await expect(page.getByRole("heading", { name: "Artists", exact: true })).toBeVisible();
  await expect(page.locator("main li h3")).toHaveCount(24);
  await page.getByRole("searchbox", { name: "Search artists" }).fill("Rembrandt");
  const countries = page.locator(".multi-filter").filter({ has: page.locator('summary[aria-label^="Countries:"]') });
  await countries.locator("summary").click();
  await countries.getByRole("searchbox", { name: "Search countries" }).fill("Netherlands");
  await countries.getByRole("radio", { name: "Netherlands", exact: true }).check();
  await countries.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page).toHaveURL(/q=Rembrandt/);
  await expect(page.locator("main").getByRole("link", { name: /^Rembrandt van Rijn 1606/ })).toBeVisible();
  await expect(page.locator("main li h3")).not.toHaveCount(24);
  await page.getByRole("searchbox", { name: "Search artists" }).fill("ArtlineNonexistentArtistName");
  await expect(page.getByRole("heading", { name: "No artists match these filters" })).toBeVisible();
  await page.getByRole("button", { name: "Show all artists", exact: true }).click();
  await expect(countries.locator("summary")).toHaveAttribute("aria-label", "Countries: All countries");
  await expect(page.getByRole("searchbox", { name: "Search artists" })).toHaveValue("");
  const first = await page.locator("main li h3").allTextContents();
  await page.getByRole("link", { name: "Next artists", exact: true }).click();
  await expect(page).toHaveURL(/cursor=/);
  await expect(page.locator("main li h3")).toHaveCount(24);
  const second = await page.locator("main li h3").allTextContents();
  expect(second.some(name => first.includes(name))).toBe(false);
  await page.getByRole("link", { name: "First artists", exact: true }).click();
  await page.getByLabel("Top 1,000 cohort").check();
  await expect(page.getByRole("heading", { name: "1,000 artists", exact: true })).toBeVisible();
});

for (const width of [1440, 390, 320]) {
  test(`one artist workspace exposes full works, biography and museums at ${width}px`, async ({ page }, info) => {
    test.setTimeout(60000);
    const museumPageRequests: string[] = [];
    page.on("request", request => { if (new URL(request.url()).pathname.startsWith("/museums/")) museumPageRequests.push(request.url()); });
    await page.setViewportSize({ width, height: 1000 });
    const artist = await (await page.request.get("/api/backend/v1/artists/rembrandt")).json() as ArtistDetail;
    expect(artist.artwork_count).toBeGreaterThan(1000);
    await page.goto("/artists/rembrandt");
    await expect(page.getByRole("heading", { name: artist.display_name, exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Biography", exact: true })).toBeVisible();
    if ((artist.biography_md?.trim().length ?? 0) >= 400) await page.locator(".reference-biography summary").click();
    await expect(page.getByRole("link", { name: "Wikipedia contributors", exact: true })).toBeVisible();
    if ((artist.biography_md?.trim().length ?? 0) >= 400) await page.locator(".reference-biography summary").click();
    const works = page.locator(".selected-works");
    await expect(works.locator(".work-card")).toHaveCount(24);
    await expect(works.getByRole("status")).toHaveText(`${artist.artwork_count!.toLocaleString("en-GB")} recorded works`);
    await page.screenshot({ path: info.outputPath(`artist-${width}.png`), fullPage: false });
    if (width < 761) await works.getByRole("button", { name: "Filters", exact: true }).click();
    await works.getByRole("combobox", { name: "Work type", exact: true }).selectOption("painting");
    await expect(page).toHaveURL(/art_type=painting/);
    const filtered = await (await page.request.get("/api/backend/v1/artists/rembrandt/works?image_only=false&work_type=painting")).json() as ArtistWorksPage;
    await expect(works.locator(".work-title").first()).toHaveText(filtered.items[0].title);
    await works.getByRole("button", { name: "Next artworks", exact: true }).click();
    await expect(page).toHaveURL(/art_cursor=/);
    await expect(works.locator(".work-title").first()).not.toHaveText(filtered.items[0].title);
    await works.getByRole("button", { name: "Reset view" }).click();
    if (width < 761) await works.getByRole("button", { name: "Filters", exact: true }).click();
    await expect(works.getByRole("combobox", { name: "Work type", exact: true })).toHaveValue("");
    const collection = page.getByRole("region", { name: "Museum holdings" });
    await expect(collection.locator("li")).toHaveCount(artist.collections!.length);
    await collection.getByRole("button", { name: "Browse works", exact: true }).first().click();
    await expect(works.locator('summary[aria-label^="Museum / collection:"]')).toContainText(artist.collections![0].name);
    await expect(works).toContainText(`${artist.collections![0].work_count.toLocaleString("en-GB")} matching works`);
    await works.locator(".work-card").first().click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(viewer).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect(museumPageRequests).toEqual([]);
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  });
}

test("Van Gogh uses the same catalogue and title search preserves biography", async ({ page }) => {
  await page.goto("/artists/vincent-van-gogh-q5582");
  await expect(page.locator(".artist-heading h1")).toHaveText("Vincent van Gogh");
  await expect(page.locator(".selected-works .work-card")).toHaveCount(24);
  await page.getByRole("searchbox", { name: "Search artworks", exact: true }).fill("ArtlineNonexistentCatalogueTitle");
  await expect(page.getByRole("heading", { name: "No matching artworks" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Biography", exact: true })).toBeVisible();
  await page.locator(".selected-works").getByRole("button", { name: "Reset view" }).first().click();
  await expect(page.locator(".selected-works .work-card")).toHaveCount(24);
});


test("one catalogue uses normal links and normalizes old visibility parameters", async ({ page, request }) => {
  const baseline = await (await request.get("/api/backend/v1/artists/rembrandt/works?limit=1")).json() as ArtistWorksPage;
  for (const query of ["preview=0", "preview=1", "status=published", "status=review"]) {
    const result = await (await request.get(`/api/backend/v1/artists/rembrandt/works?limit=1&${query}`)).json() as ArtistWorksPage;
    expect(result.total).toBe(baseline.total);
    expect(result.items[0].id).toBe(baseline.items[0].id);
  }
  await page.goto("/artists/rembrandt?catalogue=all&art_type=painting");
  await expect(page).toHaveURL(/\/artists\/rembrandt\?art_type=painting$/);
  await expect(page.getByRole("link", { name: "Browse the full recorded catalogue", exact: true })).toHaveCount(0);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /index, follow/);
  const first = baseline.items[0];
  await page.goto(`/artists/rembrandt/works/${first.id}?catalogue=all&preview=0`);
  await expect(page).toHaveURL(new RegExp(`/artists/rembrandt/works/${first.id}$`));
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(first.title);
});
