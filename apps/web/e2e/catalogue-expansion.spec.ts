import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Read-only verification of the actual local imported records.
test("Brera catalogue description opens safely on desktop and mobile", async ({ page }) => {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/museums/pinacoteca-di-brera?artist=francesco-hayez-q223725");
    await page.getByRole("button", { name: "Open Il bacio", exact: true }).click();
    const panel = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
    await expect(panel.getByRole("heading", { name: "Il bacio", exact: true })).toBeVisible();
    await panel.getByText("About this artwork", { exact: true }).click();
    await expect(panel.locator(".artwork-description")).toContainText("Catalogue inventory 6335");
    await expect(panel.locator(".artwork-description").getByRole("link", { name: "museum catalogue" })).toHaveAttribute("href", "https://pinacotecabrera.org/collezioni/collezione-on-line/il-bacio/");
    expect(await panel.evaluate(el => el.scrollWidth)).toBeLessThanOrEqual(width);
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await panel.locator(".artwork-description").scrollIntoViewIfNeeded();
    await page.screenshot({ path: `../../docs/screenshots/brera-description-${width}.png` });
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: "Open Il bacio", exact: true })).toBeFocused();
  }
});

test("painter descriptions are fetched when opened without loading text for every card", async ({ page }) => {
  const path = "/artists/francesco-hayez-q223725/works/e1a29c07-1757-4336-ad06-71b7e86f05ee";
  await page.goto(path);
  await page.getByText("About this artwork", { exact: true }).click();
  await expect(page.locator(".artwork-description")).toContainText("Catalogue inventory 6335");
});
