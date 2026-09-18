import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/", "/books", "/events", "/museums", "/catalogue"];
for (const width of [1440, 390, 320]) {
  for (const route of routes) {
    test(`shared controls on ${route} at ${width}px`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(route);
      const controls = page.locator(".atlas-filter-system");
      await expect(controls).toBeVisible();
      await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link")).toHaveText(["Painters", "Books", "Events", "All"]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      const search = controls.getByRole("searchbox");
      await page.keyboard.press("/"); await expect(search).toBeFocused();
      await expect(controls.getByRole("button", { name: "Reset view", exact: true })).toBeVisible();
      const group = controls.locator(".atlas-filter-row");
      if (width <= 760) {
        await expect(group).not.toBeVisible();
        const toggle = page.getByRole("button", { name: "Filters", exact: true });
        await toggle.click(); await expect(toggle).toHaveAttribute("aria-expanded", "true"); await expect(group).toBeVisible();
        const first = group.locator("summary, select").first(); await first.focus(); await page.keyboard.press("Escape");
        // A multiselect consumes Escape first; a second press collapses the group.
        if (await group.isVisible()) { await page.getByRole("button", { name: "Close filters", exact: true }).focus(); await page.keyboard.press("Escape"); }
        await expect(group).not.toBeVisible(); await expect(toggle).toBeFocused();
        if (["/", "/books", "/events"].includes(route)) {
          await expect(page.locator(".active-filters")).toContainText("Top 100");
          expect((await page.locator(".timeline-dark").boundingBox())!.y).toBeLessThan(350);
        }
      } else await expect(group).toBeVisible();
      await expect(page.locator('[aria-busy="true"]')).toHaveCount(0, { timeout: 15000 });
      expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
      await page.screenshot({ path: info.outputPath(`${route.replaceAll("/", "") || "art"}-${width}.png`) });
    });
  }
}

test("catalogue search and sorting survive reload and reset together", async ({ page }) => {
  await page.goto("/catalogue");
  await page.getByRole("searchbox", { name: "Search painters", exact: true }).fill("Monet");
  await page.getByLabel("Sort by", { exact: true }).selectOption("date");
  await expect(page).toHaveURL(/q=Monet/); await expect(page).toHaveURL(/sort=date/);
  await expect(page.locator(".table-shell")).toHaveAttribute("aria-busy", "false");
  await page.reload();
  await expect(page.getByRole("searchbox", { name: "Search painters", exact: true })).toHaveValue("Monet");
  await expect(page.getByLabel("Sort by", { exact: true })).toHaveValue("date");
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await expect(page.getByRole("searchbox", { name: "Search painters", exact: true })).toHaveValue("");
  await expect(page.getByLabel("Sort by", { exact: true })).toHaveValue("name");
  await expect(page.locator(".active-filters")).toHaveCount(0);
});

test("phone filters retain Russian books and restore keyboard focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/books?top100=false");
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await page.locator('summary[aria-label^="Languages:"]').click();
  await page.getByRole("checkbox", { name: "Russian", exact: true }).check();
  await page.keyboard.press("Escape");
  await expect(page.locator('summary[aria-label^="Languages:"]')).toBeFocused();
  await expect(page.locator(".atlas-filter-row")).toBeVisible();
  await page.getByRole("button", { name: "Close filters", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("505 books");
  await expect(page.locator(".active-filters")).toContainText("Russian");
  await page.reload();
  await expect(page.locator(".atlas-filter-row")).not.toBeVisible();
  await expect(page.locator(".timeline-counter")).toContainText("505 books");
  await page.getByRole("button", { name: "Remove Russian filter", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("10,000 books");
  await expect(page.getByRole("searchbox", { name: "Find a book or author" })).toBeFocused();
});

test("catalogue pagination, status and browser history stay in sync", async ({ page }) => {
  await page.goto("/catalogue");
  await page.getByRole("button", { name: "Next page", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
  await expect(page.locator(".catalogue-pagination")).toContainText("Page 2");
  await page.getByRole("combobox", { name: "Status", exact: true }).selectOption("review");
  await expect(page).toHaveURL(/status=review/);
  await expect(page.locator(".catalogue-pagination")).toContainText("Page 1");
  await page.goBack();
  await expect(page.getByRole("combobox", { name: "Status", exact: true })).toHaveValue("");
  await expect(page.locator(".catalogue-pagination")).toContainText("Page 2");
  await page.goForward();
  await expect(page.getByRole("combobox", { name: "Status", exact: true })).toHaveValue("review");
  await expect(page.locator(".catalogue-pagination")).toContainText("Page 1");
});

test("phone museum filters preserve selections outside the collapsed panel", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/museums");
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await page.locator('summary[aria-label^="Countries:"]').click();
  await page.getByRole("checkbox", { name: "Denmark", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Close filters", exact: true }).click();
  await expect(page.locator(".active-filters")).toContainText("Denmark");
  await expect(page.getByRole("heading", { name: "Skagens Museum", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await expect(page.locator(".active-filters")).toHaveCount(0);
  await expect(page.getByRole("searchbox", { name: "Search collections", exact: true })).toBeFocused();
});
