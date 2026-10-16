import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("searches guides, restores URL state, clears and follows a result", async ({ page }) => {
  await page.goto("/guides");
  const results = page.getByRole("region", { name: "Guide results" });
  const search = page.getByRole("searchbox", { name: "Search guides" });
  await expect(results.locator("article")).toHaveCount(24);
  await search.fill("frida");
  await expect(results.locator("article")).toHaveCount(1);
  await expect(results.getByRole("link", { name: "Frida Kahlo", exact: true })).toBeVisible();
  await expect(page).toHaveURL(/q=frida/);
  await page.getByRole("button", { name: /^Museums/ }).click();
  await expect(page.getByRole("heading", { name: "No guides found" })).toBeVisible();
  await page.goBack();
  await expect(results.getByRole("link", { name: "Frida Kahlo", exact: true })).toBeVisible();
  await page.reload();
  await expect(search).toHaveValue("frida");
  await results.getByRole("link", { name: "Frida Kahlo", exact: true }).click();
  await expect(page).toHaveURL(/\/guides\/frida-kahlo$/);
  await page.goBack();
  await page.getByRole("button", { name: "Clear search guides" }).click();
  await expect(results.locator("article")).toHaveCount(24);
});

test("paginates and searches locations, translated titles and the timeline guide", async ({ page }) => {
  await page.goto("/guides");
  const results = page.getByRole("region", { name: "Guide results" });
  const first = await results.locator("h3").allTextContents();
  await page.getByRole("link", { name: "Next guides" }).click();
  await expect(page).toHaveURL(/cursor=/);
  await expect(results.locator("article")).toHaveCount(24);
  expect((await results.locator("h3").allTextContents()).some(name => first.includes(name))).toBe(false);
  await page.getByRole("link", { name: "First guides" }).click();
  await expect(results.locator("h3").first()).toHaveText(first[0]);
  const search = page.getByRole("searchbox", { name: "Search guides" });
  await search.fill("Louvre Paris");
  await expect(results.getByRole("link", { name: "Louvre", exact: true })).toBeVisible();
  await search.fill("Фрида");
  await expect(results.getByRole("link", { name: "Frida Kahlo", exact: true })).toBeVisible();
  await search.fill("timeline");
  await page.getByRole("button", { name: /^Using Artline/ }).click();
  await expect(results.getByRole("link", { name: "Explore art history through time", exact: true })).toBeVisible();
});

test("mobile search is accessible and handles no matches and network recovery", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 850 });
  await page.goto("/guides?q=Prado");
  await expect(page.getByRole("heading", { name: "Museo del Prado", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const scan = await new AxeBuilder({ page }).include("#main-content").analyze();
  expect(scan.violations).toEqual([]);
  await page.getByRole("searchbox").fill("zzz_no_guide");
  await expect(page.getByRole("heading", { name: "No guides found" })).toBeVisible();
  await page.route("**/api/backend/v1/guides?*", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: { message: "Please try again." } }) }));
  await page.getByRole("button", { name: "Show all guides" }).click();
  await expect(page.getByRole("region", { name: "Guide results" }).getByRole("alert")).toContainText("Please try again.");
  await page.unroute("**/api/backend/v1/guides?*");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.getByRole("region", { name: "Guide results" }).locator("article")).toHaveCount(24);
});
