import { test, expect } from "@playwright/test";
import type { ArtistWorksPage } from "../lib/types";

const removedChronologyNote = "Recorded works, not a complete lifetime output. Ranges use their first recorded year; approximate and before/after dates keep their original labels.";
const removedDisplayNote = "Display not verified. A holding record does not mean this work is currently on view.";

for (const width of [1440, 390]) {
  test(`full painter link opens all paginated artworks at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const response = await page.request.get("/api/backend/v1/artists/claude-monet/works?image_only=false");
    await expect(response).toBeOK();
    const all = await response.json() as ArtistWorksPage;
    expect(all.total).toBeGreaterThan(24);
    const secondResponse = await page.request.get(`/api/backend/v1/artists/claude-monet/works?image_only=false&cursor=${encodeURIComponent(all.next_cursor)}`);
    await expect(secondResponse).toBeOK();
    const secondPage = await secondResponse.json() as ArtistWorksPage;
    await page.goto("/?artist=claude-monet");
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    const full = drawer.getByRole("link", { name: "Open full painter record" });
    await expect(full).toBeInViewport();
    await expect(full).toHaveAttribute("href", "/artists/claude-monet");
    expect((await full.boundingBox())!.y).toBeLessThan((await drawer.getByRole("heading", { name: "Artworks by year", exact: true }).boundingBox())!.y);
    await expect(drawer.getByText("In review", { exact: true })).toHaveCount(0);
    await expect(drawer.getByText(removedChronologyNote, { exact: true })).toHaveCount(0);
    await full.click();
    await expect(page).toHaveURL(/\/artists\/claude-monet$/);
    const chronology = page.getByRole("region", { name: "Artworks by year", exact: true });
    await expect(chronology.getByRole("checkbox", { name: "With pictures" })).not.toBeChecked();
    await expect(chronology.getByRole("status")).toHaveText(`${all.total.toLocaleString("en-GB")} recorded works`);
    await expect(chronology.locator(".work-card")).toHaveCount(24);
    await expect(chronology.locator(".work-title").first()).toHaveText(all.items[0].title);
    await expect(page.getByText(removedChronologyNote, { exact: true })).toHaveCount(0);
    await expect(page.getByText(removedDisplayNote, { exact: true })).toHaveCount(0);
    await expect(page.getByText("In review", { exact: true })).toHaveCount(0);
    await expect(page.locator(".record-toolbar")).not.toContainText(/in review/i);
    await chronology.getByRole("button", { name: "Next artworks", exact: true }).click();
    await expect(chronology.locator(".work-title").first()).toHaveText(secondPage.items[0].title);
    await expect(chronology.locator(".work-card")).toHaveCount(secondPage.items.length);
    const card = chronology.locator(".work-card").first();
    await expect(page.locator(".artwork-panel")).toHaveCount(0);
    await card.click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer.getByRole("heading", { level: 2 })).toHaveText(secondPage.items[0].title);
    await expect(page.locator(".artist-heading h1")).toHaveText("Claude Monet");
    await expect(page).toHaveTitle(/Claude Monet/);
    await expect(viewer.locator(".image-dialog-artist")).toContainText("Claude Monet");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`full-painter-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(viewer).toHaveCount(0);
    await expect(card).toBeFocused();
    await chronology.getByRole("button", { name: "Previous artworks", exact: true }).click();
    await expect(chronology.locator(".work-title").first()).toHaveText(all.items[0].title);
  });
}

test("a directly linked artwork keeps the painter's complete chronology and enlarged navigation", async ({ page }) => {
  const response = await page.request.get("/api/backend/v1/artists/claude-monet/works?image_only=true");
  await expect(response).toBeOK();
  const works = await response.json() as ArtistWorksPage;
  const [first, second] = works.items;
  await page.goto(`/artists/claude-monet/works/${first.id}?art_images=true`);
  const chronology = page.locator(".selected-works");
  await expect(chronology.locator(".work-card")).toHaveCount(24);
  await expect(page.locator(".artwork-panel")).toHaveCount(0);
  const large = page.getByRole("dialog", { name: /Enlarged image:/ });
  await large.getByRole("button", { name: "Next artwork", exact: true }).click();
  await expect(large.getByRole("heading")).toHaveText(second.title);
  await large.getByRole("button", { name: "Previous artwork", exact: true }).click();
  await expect(large.getByRole("heading")).toHaveText(first.title);
  await page.keyboard.press("Escape");
  await expect(large).toHaveCount(0);
});

test("canonical artwork links and records remain available without JavaScript", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    await page.goto(`${test.info().project.use.baseURL}/artists/claude-monet`);
    const link = page.getByRole("navigation", { name: "Artwork pages" }).getByRole("link").first();
    const title = await link.innerText();
    await link.click();
    await expect(page).toHaveURL(/\/artists\/claude-monet\/works\//);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    await expect(page.locator(".artwork-details h3")).toHaveText(title);
    const id = new URL(page.url()).pathname.split("/").at(-1)!;
    const redirect = await page.request.get(`${test.info().project.use.baseURL}/artists/claude-monet?work=${id}&art_images=true&art_year=1855`, { maxRedirects: 0 });
    expect(redirect.status()).toBe(308);
    const location = new URL(redirect.headers().location, page.url());
    expect(location.pathname).toBe(`/artists/claude-monet/works/${id}`);
    expect(location.searchParams.get("art_images")).toBe("true");
    expect(location.searchParams.get("art_year")).toBe("1855");
  } finally { await context.close(); }
});
