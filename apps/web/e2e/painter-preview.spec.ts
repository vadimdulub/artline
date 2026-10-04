import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistWorksPage } from "../lib/types";

for (const width of [1440, 390, 320]) {
  test(`painter preview puts a large picture before collapsed filters at ${width}px`, async ({ page }, info) => {
    test.setTimeout(60000);
    await page.setViewportSize({ width, height: 900 });
    const response = await page.request.get("/api/backend/v1/artists/claude-monet/works?image_only=true");
    expect(response.ok()).toBe(true);
    const pictures = await response.json() as ArtistWorksPage;
    await page.goto("/?q=Monet");
    await page.locator(".artist-mark").filter({ hasText: "Claude Monet" }).click();
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    const preview = drawer.getByRole("complementary", { name: "Artwork preview" });
    const image = preview.locator(".artwork-image > img");
    await expect(image).toBeInViewport();
    await image.evaluate((node: HTMLImageElement) => node.decode());
    const pictureBox = (await image.boundingBox())!;
    expect(pictureBox.height).toBeGreaterThanOrEqual(250);
    expect(pictureBox.y + pictureBox.height).toBeLessThanOrEqual(900);
    await expect(preview.locator("h3")).toHaveText(pictures.items[0].title);
    await expect(drawer.getByRole("button", { name: "Artwork filters", exact: true })).toHaveAttribute("aria-expanded", "false");
    await expect(drawer.getByRole("searchbox", { name: "Search artworks", exact: true })).toHaveCount(0);
    await expect(drawer.locator(".work-card")).toHaveCount(24);
    expect((await drawer.locator(".selected-works").boundingBox())!.y).toBeGreaterThan(pictureBox.y + pictureBox.height);
    await page.screenshot({ path: info.outputPath(`picture-first-${width}.png`) });

    await preview.getByRole("button", { name: "Next artwork", exact: true }).click();
    await expect(preview.locator("h3")).toHaveText(pictures.items[1].title);
    await preview.getByRole("button", { name: "Previous artwork", exact: true }).click();
    await expect(preview.locator("h3")).toHaveText(pictures.items[0].title);
    await preview.getByRole("button", { name: /View larger/ }).click();
    const enlarged = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(enlarged).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(enlarged).toHaveCount(0);
    await expect(drawer).toBeVisible();
    await preview.getByRole("button", { name: "Browse artworks", exact: true }).click();
    const firstGrid = drawer.locator(".works-list").first();
    expect(await firstGrid.evaluate(node => getComputedStyle(node).gridTemplateColumns.split(" ").length)).toBe(2);
    await drawer.locator(".work-card").nth(1).click();
    await expect(preview.locator("h3")).toHaveText(pictures.items[1].title);
    await expect(image).toBeInViewport();

    const filters = drawer.getByRole("button", { name: "Artwork filters", exact: true });
    await filters.click();
    await expect(drawer.getByRole("checkbox", { name: "With pictures" })).toBeChecked();
    await drawer.getByRole("searchbox", { name: "Search artworks", exact: true }).fill("ArtlineNonexistentCatalogueTitle");
    await drawer.getByRole("button", { name: "Search works", exact: true }).click();
    await expect(drawer.getByRole("heading", { name: "No matching artworks" })).toBeVisible();
    await expect(preview).toHaveCount(0);
    await drawer.getByRole("button", { name: "Clear artwork filters", exact: true }).first().click();
    await expect(drawer.getByRole("checkbox", { name: "With pictures" })).not.toBeChecked();
    await expect(drawer.locator(".work-card")).toHaveCount(24);
    await filters.click();
    await expect(filters).toHaveAttribute("aria-expanded", "false");
    expect(await drawer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual((await drawer.boundingBox())!.width);
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  });
}
