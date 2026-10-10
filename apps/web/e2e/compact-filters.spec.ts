import { expect, test } from "@playwright/test";

const painterURL = "/?painter=michelangelo-q5592&painter=vincent-van-gogh-q5582&popular=false";

test("desktop filter controls stay compact with selected painters", async ({ page }, info) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(painterURL);
  const filters = page.locator(".atlas-filter-system").first();
  await expect(filters.locator(".search-field input")).toBeVisible();
  await expect(filters.getByRole("checkbox", { name: "Women artists", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Remove Michelangelo filter", exact: true })).toBeVisible();
  expect((await filters.boundingBox())!.height).toBeLessThanOrEqual(84);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(1440);
  await page.screenshot({ path: info.outputPath("desktop-compact-filters.png") });
});

for (const width of [320, 390]) {
  for (const route of [painterURL, "/books?top100=false", "/events?top100=false", "/all?selection=true&type=book&start=1800&end=1900"]) {
    test(`mobile filters give space to content at ${width}px on ${route.split("?")[0]}`, async ({ page }, info) => {
      await page.setViewportSize({ width, height: 844 });
      await page.goto(route);
      const filters = page.locator(".atlas-filter-system").first();
      const toggle = filters.getByRole("button", { name: "Filters", exact: true });
      const search = filters.locator(".search-field input");
      await expect(toggle).toBeVisible();
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
      await expect(search).toBeHidden();
      expect((await filters.boundingBox())!.height).toBeLessThanOrEqual(48);
      await expect(page.locator(".active-filters").first()).not.toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      await page.screenshot({ path: info.outputPath("mobile-content.png") });
      await toggle.click();
      await expect(search).toBeVisible();
      await search.focus();
      await page.keyboard.press("Escape");
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
      await expect(toggle).toBeFocused();
      await page.keyboard.press("/");
      await expect(search).toBeVisible();
      await expect(search).toBeFocused();
      await filters.getByRole("button", { name: "Close filters", exact: true }).click();
      await expect(search).toBeHidden();
      await expect(toggle).toBeFocused();
    });
  }
}

test("mobile search survives closing filters and full view restores content", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?popular=false&q=Rembrandt");
  const filters = page.locator(".atlas-filter-system").first();
  const toggle = filters.getByRole("button", { name: "Filters", exact: true });
  await expect(toggle.locator(".atlas-filter-count")).toHaveText("1");
  await toggle.click();
  await expect(filters.locator(".search-field input")).toHaveValue("Rembrandt");
  await filters.getByRole("button", { name: "Close filters", exact: true }).click();
  await expect(page).toHaveURL(/q=Rembrandt/);
  await filters.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "true");
  await toggle.click();
  await expect(filters.locator(".search-field input")).toHaveValue("Rembrandt");
  await page.keyboard.press("Escape");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "true");
  await page.keyboard.press("Escape");
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "false");
  await page.screenshot({ path: info.outputPath("mobile-restored.png") });
});
