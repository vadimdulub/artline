import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Catalogue reads only. Signed-out state is simulated in the browser, never in the database.
for (const width of [320, 390, 430]) {
  test(`mobile navigation gives content the full width at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/artists");
    await expect(page.getByRole("heading", { name: "Artists", exact: true })).toBeVisible();
    const header = page.locator(".site-header");
    await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
    await expect(page.locator(".member-sidebar")).toBeHidden();
    await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeHidden();
    expect((await header.boundingBox())!.height).toBeLessThanOrEqual(112);
    for (const link of await header.locator(".primary-nav a:visible").all()) {
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`artists-${width}.png`) });
    const menuButton = page.getByRole("button", { name: "Menu", exact: true });
    await menuButton.click();
    const menu = page.getByRole("dialog", { name: "Explore Artline" });
    await expect(menu).toBeVisible();
    await expect(page.locator("body")).toHaveCSS("overflow", "hidden");
    for (const link of await menu.getByRole("link").all()) {
      await expect(link).toBeInViewport();
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    await page.keyboard.press("Escape");
    await expect(menu).toBeHidden();
    await expect(menuButton).toBeFocused();
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
    await menuButton.click();
    await menu.getByRole("link", { name: "Museums", exact: true }).click();
    await expect(page).toHaveURL(/\/museums$/);
    await expect(menu).toBeHidden();
    await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  });
}

test("mobile menu preserves museum sign-in and nested focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.goto("/");
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  const menu = page.getByRole("dialog", { name: "Explore Artline" });
  await menu.getByRole("link", { name: "Museums", exact: true }).click();
  const signIn = page.getByRole("dialog", { name: "Sign in to Artline" });
  await expect(signIn).toBeVisible();
  await expect(signIn.locator("form")).toHaveAttribute("action", /return_to=%2Fmuseums/);
  await page.keyboard.press("Escape");
  await expect(signIn).toBeHidden();
  await expect(menu.getByRole("link", { name: "Museums", exact: true })).toBeFocused();
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await menu.getByRole("link", { name: "Artists", exact: true }).click();
  await expect(page).toHaveURL(/\/artists$/);
  await expect(menu).toBeHidden();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});

test("phone filters stay attached to their labels and clearing does not open the keyboard", async ({ page }, info) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto("/");
  const filters = page.getByRole("button", { name: "Filters", exact: true });
  await filters.click();
  const countries = page.locator(".multi-filter").filter({ has: page.locator('summary[aria-label^="Countries:"]') });
  await countries.locator("summary").click();
  expect((await countries.locator("summary").boundingBox())!.height).toBeLessThan(100);
  await expect(countries.locator(".multi-filter-panel")).toHaveCSS("position", "relative");
  await countries.getByRole("searchbox").fill("France");
  await countries.getByRole("checkbox", { name: "France", exact: true }).check();
  await expect(page).toHaveURL(/country=FR/);
  await countries.getByRole("button", { name: "Done", exact: true }).click();
  await page.getByRole("button", { name: "Close filters", exact: true }).click();
  await expect(filters).toBeFocused();
  // Active filter chips are inside the expandable phone controls.
  await filters.click();
  await page.getByRole("button", { name: "Remove France filter", exact: true }).click();
  await expect(page).not.toHaveURL(/country=FR/);
  await expect(page.getByRole("searchbox").first()).not.toBeFocused();
  await expect(filters).toBeFocused();
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await expect(filters).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await page.screenshot({ path: info.outputPath("mobile-filter-results.png") });
});

test("menu releases its scroll lock when rotating into the desktop layout", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  await page.setViewportSize({ width: 1024, height: 768 });
  await expect(page.getByRole("dialog", { name: "Explore Artline" })).toBeHidden();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  await expect(page.locator(".site-header").getByRole("link", { name: "Your account", exact: true })).toBeVisible();
});
