import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistWorksPage } from "../lib/types";

for (const width of [1440, 390, 320]) {
  test(`Friedrich's artworks appear before tags and smaller museum links at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?q=Friedrich");
    await page.locator(".artist-mark").filter({ hasText: "Caspar David Friedrich" }).click();
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    const name = drawer.getByRole("heading", { name: "Caspar David Friedrich", exact: true });
    await expect(name).toBeInViewport();
    const works = drawer.locator(".selected-works");
    await expect(works.locator(".work-row").first()).toBeInViewport();
    const nameBounds = (await name.boundingBox())!;
    const worksBounds = (await works.boundingBox())!;
    const tagsBounds = (await drawer.locator(".record-classification").boundingBox())!;
    expect(nameBounds.y + nameBounds.height).toBeLessThan(worksBounds.y);
    expect(worksBounds.y + worksBounds.height).toBeLessThan(tagsBounds.y);
    const museums = drawer.getByRole("navigation", { name: "Collections for these artworks" });
    expect((await museums.boundingBox())!.y).toBeGreaterThan(worksBounds.y + worksBounds.height);
    for (const link of await museums.getByRole("link").all()) {
      expect((await link.boundingBox())!.height).toBeLessThanOrEqual(52);
      expect(await link.evaluate(node => parseFloat(getComputedStyle(node).fontSize))).toBeLessThanOrEqual(12);
    }
    expect(await drawer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath(`friedrich-artworks-first-${width}.png`) });
  });

  test(`full painter gallery opens a picture with details and fixed arrows at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const response = await page.request.get("/api/backend/v1/artists/claude-monet/works?image_only=true");
    await expect(response).toBeOK();
    const works = await response.json() as ArtistWorksPage;
    const last = works.items.at(-1)!;
    const neighborResponse = await page.request.get(`/api/backend/v1/artists/claude-monet/works?image_only=true&neighbor_of=${last.id}&direction=next&limit=1`);
    await expect(neighborResponse).toBeOK();
    const neighbor = await neighborResponse.json() as ArtistWorksPage;
    await page.goto("/artists/claude-monet?art_images=true");
    const chronology = page.getByRole("region", { name: "Artworks by year", exact: true });
    const cards = chronology.locator(".work-card");
    await expect(cards).toHaveCount(24);
    await expect(page.locator(".artwork-panel")).toHaveCount(0);
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(cards.first()).toBeInViewport();
    expect((await cards.first().locator("img").boundingBox())!.width).toBeGreaterThan(200);
    await page.screenshot({ path: info.outputPath(`painter-gallery-${width}.png`) });
    await cards.last().click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer.getByRole("heading", { level: 2 })).toHaveText(last.title);
    await expect(viewer.getByRole("button", { name: "Zoom in" })).toBeEnabled();
    const next = viewer.getByRole("button", { name: "Next artwork", exact: true });
    const previous = viewer.getByRole("button", { name: "Previous artwork", exact: true });
    const nextBefore = (await next.boundingBox())!;
    const previousBefore = (await previous.boundingBox())!;
    await viewer.getByText("Artwork details and sources", { exact: true }).click();
    await expect(viewer.getByText("Medium", { exact: true })).toBeVisible();
    await expect(viewer.getByText("Image rights", { exact: true })).toBeVisible();
    await next.click();
    await expect(viewer.getByRole("heading", { level: 2 })).toHaveText(neighbor.items[0].title);
    expect(await next.boundingBox()).toEqual(nextBefore);
    expect(await previous.boundingBox()).toEqual(previousBefore);
    await expect(previous).toBeEnabled();
    await previous.press("Enter");
    await expect(viewer.getByRole("heading", { level: 2 })).toHaveText(last.title);
    expect(await next.boundingBox()).toEqual(nextBefore);
    expect(await viewer.evaluate(node => node.scrollHeight <= node.clientHeight)).toBe(true);
    expect(await viewer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    if (width === 390) {
      const scan = await new AxeBuilder({ page }).include('.image-dialog[open]').withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
      expect(scan.violations).toEqual([]);
    }
    await page.screenshot({ path: info.outputPath(`gallery-viewer-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(viewer).toHaveCount(0);
    await expect(cards.last()).toBeFocused();
    await expect(page.locator(".artwork-panel")).toHaveCount(0);
    await cards.last().press("Enter");
    await expect(viewer.getByRole("heading", { level: 2 })).toHaveText(last.title);
    await viewer.getByRole("button", { name: "Close enlarged image" }).click();
    await expect(cards.last()).toBeFocused();
  });
}
