import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Public navigation must work without a member session or database fixtures.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
});

test("Guides opens the existing article and remains the active section", async ({ page }, info) => {
  await page.goto("/guides");
  const header = page.locator(".site-header");
  const guides = header.getByRole("link", { name: "Guides", exact: true });
  await expect(page.getByRole("heading", { name: "Guides", exact: true })).toBeVisible();
  await expect(guides).toHaveAttribute("aria-current", "page");
  await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeVisible();
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  for (const width of [1440, 1024, 900, 768]) {
    await page.setViewportSize({ width, height: 1000 });
    expect((await header.boundingBox())!.height).toBe(60);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await expect(guides).toBeInViewport();
    await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeInViewport();
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath("guides-desktop.png") });
  await page.getByRole("link", { name: "Read the guide", exact: true }).click();
  await expect(page).toHaveURL(/\/art-history-timeline$/);
  await expect(page.getByRole("heading", { name: "Explore art history through time", exact: true })).toBeVisible();
  await expect(guides).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  await expect(guides).toHaveAttribute("aria-current", "page");
  await page.getByRole("navigation", { name: "Breadcrumb" }).getByRole("link", { name: "Guides", exact: true }).click();
  await expect(page).toHaveURL(/\/guides$/);
});

test("mobile visitors reach Guides and Account from the menu", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/about");
  const menuButton = page.getByRole("button", { name: "Menu", exact: true });
  await menuButton.click();
  const menu = page.getByRole("dialog", { name: "Explore Artline" });
  await menu.getByRole("link", { name: "Guides", exact: true }).click();
  await expect(page).toHaveURL(/\/guides$/);
  await expect(menu).toBeHidden();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  await expect(page.getByRole("heading", { name: "Guides", exact: true })).toBeVisible();
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect((await page.locator(".site-header").boundingBox())!.height).toBeLessThanOrEqual(112);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: info.outputPath("guides-mobile.png") });
  await menuButton.click();
  await expect(menu.getByRole("link", { name: "Guides", exact: true })).toHaveAttribute("aria-current", "page");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await menu.getByRole("link", { name: "Your account", exact: true }).click();
  await expect(page).toHaveURL(/\/account$/);
  await expect(page.getByRole("button", { name: "Sign in with Google", exact: true })).toBeVisible();
});
