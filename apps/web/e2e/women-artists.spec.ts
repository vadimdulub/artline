import { test, expect } from "@playwright/test";

async function settled(page: import("@playwright/test").Page) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(/painters? in this view/);
}

test("women filter precedes popularity, combines independently and survives navigation", async ({ page }) => {
  await page.goto("/");
  await settled(page);
  const women = page.getByRole("checkbox", { name: "Women artists", exact: true });
  const popular = page.getByRole("checkbox", { name: "Top 100 painters", exact: true });
  const labels = await page.locator(".popular-filter").allTextContents();
  expect(labels).toEqual(["Women artists", "Top 100 painters"]);
  await expect(women).not.toBeChecked();
  await expect(popular).toBeChecked();
  await women.check();
  await expect(page).toHaveURL(/women=true/);
  await settled(page);
  const combined = await (await page.request.get("/api/backend/v1/timeline?women=true")).json();
  expect(combined.women_only).toBe(true);
  expect(combined.popular_only).toBe(true);
  expect(combined.total).toBeGreaterThan(0);
  await expect(page.locator(".timeline-counter")).toContainText(`${combined.total} painters`);
  await popular.uncheck();
  await settled(page);
  const allWomen = await (await page.request.get("/api/backend/v1/timeline?women=true&popular=false")).json();
  expect(allWomen.total).toBeGreaterThan(combined.total);
  await expect(page.locator(".timeline-counter")).toContainText(`${allWomen.total} painters`);
  await page.reload();
  await settled(page);
  await expect(women).toBeChecked();
  await expect(popular).not.toBeChecked();
  await page.goBack();
  await settled(page);
  await expect(women).toBeChecked();
  await expect(popular).toBeChecked();
  await page.locator(".reset-button").click();
  await settled(page);
  await expect(women).not.toBeChecked();
  await expect(popular).toBeChecked();
  await women.check();
  await settled(page);
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await settled(page);
  await expect(women).not.toBeChecked();
  await expect(popular).not.toBeChecked();
});

test("women and popularity controls fit desktop and phone widths", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/?women=true");
    await settled(page);
    await expect(page.getByRole("checkbox", { name: "Women artists", exact: true })).toBeVisible();
    await expect(page.getByRole("checkbox", { name: "Top 100 painters", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: `/tmp/artline-women-${width}.png`, fullPage: true });
  }
});
