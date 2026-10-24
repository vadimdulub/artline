import { expect, test } from "@playwright/test";
import { mockResponsiveFilters } from "./responsive-filter-fixture";

test.beforeEach(async ({ page }) => {
  await mockResponsiveFilters(page);
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: { id: "responsive-ui", name: "UI test", email: "ui@example.invalid" } } }));
  await page.route("**/api/bookmarks/state?**", route => route.fulfill({ json: { saved: [] } }));
});

for (const route of ["/artists", "/museums", "/artworks", "/exhibitions"]) {
  for (const width of [390, 768, 1024, 1440]) test(`member ${route}: filters fit the sidebar at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(route);
    const sidebar = page.getByRole("complementary", { name: "Account navigation", exact: true });
    const scope = page.locator(".atlas-filter-system").first();
    if (width <= 760) {
      await expect(page.locator("#member-sidebar")).toHaveCount(1);
      await expect(sidebar).toBeHidden();
      await scope.getByRole("button", { name: "Filters", exact: true }).click();
    } else {
      await expect(sidebar).toBeVisible();
      await expect(page.locator("body")).toHaveCSS("padding-left", width <= 900 ? "64px" : "208px");
      const side = (await sidebar.boundingBox())!;
      await expect.poll(async () => (await scope.boundingBox())!.x).toBeGreaterThanOrEqual(side.x + side.width);
    }
    const summary = scope.locator(".multi-filter>summary").first();
    if (await summary.count()) {
      await summary.click();
      const panel = scope.locator(".multi-filter[open]>.multi-filter-panel");
      await expect(async () => {
        const box = (await panel.boundingBox())!;
        expect(box.x).toBeGreaterThanOrEqual(0);
        expect(box.x + box.width).toBeLessThanOrEqual(width);
      }).toPass({ timeout: 2000 });
      await panel.getByRole("searchbox").focus();
      await page.keyboard.press("Escape");
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width >= 1024) {
      const before = (await scope.boundingBox())!.width;
      await sidebar.getByRole("button", { name: "Collapse account panel", exact: true }).click();
      await expect(sidebar).toHaveCSS("width", "56px");
      await expect.poll(async () => (await scope.boundingBox())!.width).toBeGreaterThan(before + 150);
      await sidebar.getByRole("button", { name: "Expand account panel", exact: true }).click();
      await expect.poll(async () => (await scope.boundingBox())!.width).toBeCloseTo(before, 0);
    }
    await page.screenshot({ path: info.outputPath(`member-${route.slice(1)}-${width}.png`) });
  });
}
