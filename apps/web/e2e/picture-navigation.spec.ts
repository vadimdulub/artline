import { test, expect } from "@playwright/test";
import type { ArtistWorksPage } from "../lib/types";
import type { AtlasResponse } from "../lib/atlas";

for (const width of [1440, 390, 320]) {
  test(`creator picture filter and enlarged navigation cross pages at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const endpoint = "/api/backend/v1/artists/claude-monet/works";
    const all = await (await page.request.get(endpoint)).json() as ArtistWorksPage;
    const illustrated = await (await page.request.get(`${endpoint}?image_only=true`)).json() as ArtistWorksPage;
    expect(illustrated.total).toBeGreaterThan(24);
    expect(illustrated.total).toBeLessThan(all.total);
    const last = illustrated.items.at(-1)!;
    const next = await (await page.request.get(`${endpoint}?image_only=true&neighbor_of=${last.id}&direction=next&limit=1`)).json() as ArtistWorksPage;
    expect(next.items).toHaveLength(1);
    await page.goto("/?artist=claude-monet&art_images=true");
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    await expect(drawer.getByRole("checkbox", { name: "With pictures" })).toBeChecked();
    await expect(drawer.locator(".work-row")).toHaveCount(24);
    expect(await page.locator(".explorer .filters").getByRole("checkbox", { name: "With pictures" }).count()).toBe(0);
    await drawer.locator(".work-row").last().click();
    await drawer.getByRole("button", { name: /View larger/ }).click();
    const large = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(large.getByRole("heading")).toHaveText(last.title);
    await expect(large.getByRole("button", { name: "Next artwork", exact: true })).toBeEnabled();
    await large.getByRole("button", { name: "Next artwork", exact: true }).click();
    await expect(large.getByRole("heading")).toHaveText(next.items[0].title);
    await expect(large).toBeVisible();
    await expect(large.locator("img")).toHaveJSProperty("complete", true);
    await large.getByRole("button", { name: "Previous artwork", exact: true }).click();
    await expect(large.getByRole("heading")).toHaveText(last.title);
    expect(await large.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(width);
    for (const label of ["Next artwork", "Previous artwork"]) {
      const bounds = await large.getByRole("button", { name: label, exact: true }).boundingBox();
      expect(bounds!.height).toBeGreaterThanOrEqual(44);
      expect(bounds!.width).toBeGreaterThanOrEqual(44);
    }
    await page.screenshot({ path: info.outputPath(`enlarged-${width}.png`) });
    await large.getByRole("button", { name: "Close enlarged image" }).click();
    await drawer.getByRole("button", { name: "Next artwork", exact: true }).click();
    await expect(drawer.locator(".artwork-details h3")).toHaveText(next.items[0].title);
    await expect(drawer.getByRole("button", { name: "Next artwork", exact: true })).toBeInViewport();
    await drawer.getByRole("checkbox", { name: "With pictures" }).uncheck();
    await expect(page).not.toHaveURL(/art_images=true/);
    await expect(drawer.getByRole("region", { name: "Artworks by year", exact: true }).getByRole("status")).toContainText(all.total.toLocaleString("en-GB"));
  });
}

test("All has fixed pictures, switchable default highlights, and previous/next browse pages", async ({ page }) => {
  await page.goto("/all?start=1700&end=1970");
  await expect(page.getByRole("checkbox", { name: "Highlights", exact: true })).toBeChecked();
  await expect(page.getByRole("checkbox", { name: "With pictures" })).toHaveCount(0);
  await page.getByRole("checkbox", { name: "Highlights", exact: true }).uncheck();
  await expect(page).toHaveURL(/highlights=false/);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false", { timeout: 15000 });
  await page.getByRole("button", { name: "Browse artworks", exact: true }).click();
  const browse = page.getByRole("dialog", { name: "Browse artworks", exact: true });
  const titles = browse.locator(".atlas-picker-list strong");
  await expect(titles).toHaveCount(30);
  const first = await titles.first().innerText();
  await browse.getByRole("button", { name: /Next page/ }).click();
  await expect(titles.first()).not.toHaveText(first);
  await browse.getByRole("button", { name: /Previous page/ }).click();
  await expect(titles.first()).toHaveText(first);
  const last = await titles.last().innerText();
  await browse.getByRole("button", { name: `View ${last}`, exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Artwork details", exact: true });
  await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(last);
  await drawer.getByRole("button", { name: /View larger/ }).click();
  const large = page.getByRole("dialog", { name: /Enlarged image:/ });
  await large.getByRole("button", { name: "Next artwork", exact: true }).click();
  await expect(large.getByRole("heading")).not.toHaveText(last);
  await large.getByRole("button", { name: "Previous artwork", exact: true }).click();
  await expect(large.getByRole("heading")).toHaveText(last);
});

for (const type of ["book", "event"] as const) {
  test(`All ${type} arrows navigate a directly linked filtered entry`, async ({ page }) => {
    const query = `type=${type}&start=1800&end=1950&highlights=false`;
    const data = await (await page.request.get(`/api/backend/v1/atlas?${query}&limit=2`)).json() as AtlasResponse;
    const [first, second] = data.lanes[0].items;
    await page.goto(`/all?${query}&itemType=${type}&item=${first.id}`);
    const drawer = page.getByRole("dialog", { name: type === "book" ? "Book details" : "Event details", exact: true });
    await expect(drawer.getByRole("button", { name: `Previous ${type}`, exact: true })).toBeDisabled();
    await drawer.getByRole("button", { name: `Next ${type}`, exact: true }).click();
    await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(second.title);
    await drawer.getByRole("button", { name: `Previous ${type}`, exact: true }).click();
    await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(first.title);
    await expect(page).toHaveURL(/highlights=false/);
  });
}
