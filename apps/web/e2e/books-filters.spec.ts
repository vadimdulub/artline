import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Read-only UI/API checks against the real researched catalogue.
async function count(page: import("@playwright/test").Page, value: number) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(`${value.toLocaleString("en-GB")} books`);
}

test("book discovery checkboxes combine, restore history and reset", async ({ page }) => {
  await page.goto("/books");
  await count(page, 100);
  const women = page.getByRole("checkbox", { name: "Women authors", exact: true });
  const top = page.getByRole("checkbox", { name: "Top 100 books", exact: true });
  await expect(women).not.toBeChecked();
  await expect(top).toBeChecked();
  await top.uncheck();
  await count(page, 8685);
  await expect(page).toHaveURL(/top100=false/);
  await page.reload();
  await count(page, 8685);
  await expect(top).not.toBeChecked();
  await page.goBack();
  await count(page, 100);
  await expect(top).toBeChecked();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(100);
  await women.check();
  await count(page, 19);
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(19);
  await page.reload();
  await count(page, 19);
  await expect(women).toBeChecked();
  await expect(top).toBeChecked();
  await page.goBack();
  await count(page, 100);
  await expect(women).not.toBeChecked();
  await women.check();
  await count(page, 19);
  await page.getByRole("button", { name: "Remove Top 100 books filter", exact: true }).click();
  await count(page, 832);
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await count(page, 100);
  await expect(women).not.toBeChecked();
  await expect(top).toBeChecked();
  await expect(page.getByLabel("Find a book or author")).toBeFocused();
});

test("languages, regions and countries intersect with women and the Top 100", async ({ page }, testInfo) => {
  await page.goto("/books?women=true&top100=true");
  await count(page, 19);
  for (const [filter, name] of [["Languages", "French"], ["Regions", "Western Europe"], ["Countries", "France"]]) {
    await page.locator(`summary[aria-label^="${filter}:"]`).click();
    await page.getByRole("checkbox", { name, exact: true }).check();
    await page.getByRole("button", { name: "Done", exact: true }).click();
  }
  await count(page, 1);
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Open The Second Sex by Simone de Beauvoir", exact: true })).toBeVisible();
  const params = new URL(page.url()).searchParams;
  expect(params.get("language")).toBe("Q150");
  expect(params.get("region")).toBe("western-europe");
  expect(params.get("country")).toBe("Q142");
  await page.reload();
  await count(page, 1);
  await expect(page.locator('summary[aria-label="Languages: French"]')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("books-combined-filters.png") });
  await page.locator('summary[aria-label^="Countries:"]').click();
  await page.getByRole("checkbox", { name: "France", exact: true }).uncheck();
  await page.getByRole("checkbox", { name: "Japan", exact: true }).check();
  await page.keyboard.press("Escape");
  await count(page, 0);
  await expect(page.getByText(/No books match/)).toBeVisible();
  await page.getByRole("button", { name: "Clear filters", exact: true }).first().click();
  await count(page, 8685);
});

test("shared filter bar fits small screens, accessible tooltip and retries facets", async ({ page }, testInfo) => {
  let fail = true;
  await page.route("**/api/backend/v1/books/facets?**", route => fail ? route.fulfill({ status: 503, json: { error: { message: "Temporary test outage" } } }) : route.continue());
  await page.goto("/books");
  await count(page, 100);
  await expect(page.getByText("Some filter choices could not be loaded.")).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "Retry filters", exact: true }).click();
  await expect(page.getByText("Some filter choices could not be loaded.")).toHaveCount(0);
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books?top100=true");
    await count(page, 100);
    if (width <= 760) await page.getByRole("button", { name: "Filters", exact: true }).click();
    expect(await page.locator(".atlas-filter-row > .multi-filter summary > span:first-child").allTextContents()).toEqual(["Authors", "Regions", "Countries", "Languages"]);
    await page.getByRole("button", { name: "About the Top 100 book selection", exact: true }).focus();
    await expect(page.getByRole("tooltip")).toContainText("editorial");
    const tip = (await page.getByRole("tooltip").boundingBox())!;
    expect(tip.x).toBeGreaterThanOrEqual(0);
    expect(tip.x + tip.width).toBeLessThanOrEqual(width);
    await page.keyboard.press("Escape");
    await expect(page.getByRole("tooltip")).toHaveCount(0);
    if (width <= 760) await page.getByRole("button", { name: "Close filters", exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440) expect((await page.locator(".timeline-dark").boundingBox())!.height).toBeGreaterThan(650);
    await page.getByLabel("Book start year").hover();
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations.map(v => v.id)).toEqual([]);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: testInfo.outputPath(`books-filters-${width}.png`) });
  }
});
