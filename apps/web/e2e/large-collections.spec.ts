import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("large collection supports compact layout and reversible bounded pages", async ({ page }) => {
  await page.goto("/museums/the-met");
  const results = page.getByRole("region", { name: "Museum artwork results" });
  await expect(results.getByRole("button").first()).toBeVisible();
  await expect(results.getByRole("button")).toHaveCount(24);
  expect((await results.boundingBox())!.y).toBeLessThan(740);
  const first = await results.getByRole("button").first().getAttribute("aria-label");
  await page.getByRole("group", { name: "Artwork layout" }).getByRole("button", { name: "List", exact: true }).click();
  await expect(results.locator("ul")).toHaveAttribute("data-layout", "list");
  const pages = page.getByRole("navigation", { name: "Artwork pages above results" });
  await pages.getByRole("button", { name: "Next page", exact: true }).click();
  await expect(results.getByRole("button").first()).not.toHaveAttribute("aria-label", first!);
  await expect(results.getByRole("button")).toHaveCount(24);
  await pages.getByRole("button", { name: "Previous page", exact: true }).click();
  await expect(results.getByRole("button").first()).toHaveAttribute("aria-label", first!);
  await page.getByRole("combobox", { name: "Artworks per page" }).selectOption("48");
  await expect(results.getByRole("button")).toHaveCount(48);
  await page.getByRole("checkbox", { name: "With an available image" }).check();
  await expect(results.locator(".work-placeholder")).toHaveCount(0);
  await expect(results.getByRole("button").first()).toBeVisible();
  await results.getByRole("button").first().click();
  await expect(page.getByRole("dialog", { name: "Museum artwork details" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(results.getByRole("button").first()).toBeFocused();
});

test("large collection remains readable and accessible at desktop and phone widths", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/museums/the-met?view=list");
    await expect(page.getByRole("region", { name: "Museum artwork results" }).getByRole("button").first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: `../../docs/screenshots/large-collection-list-${width}.png` });
    await page.getByRole("group", { name: "Artwork layout" }).getByRole("button", { name: "Grid", exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: `../../docs/screenshots/large-collection-grid-${width}.png` });
  }
});
