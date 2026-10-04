import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Member previews use the real API's loopback-only debug session. No database fixtures.
test("member navigation exposes collection pages and shares the existing account session", async ({ page, request }, info) => {
  const session = await (await request.get("/api/auth/session")).json();
  expect(session.local_debug).toBe(true);
  let sessionRequests = 0;
  page.on("request", req => { if (req.url().endsWith("/api/auth/session")) sessionRequests++; });
  await page.goto("/about");
  const header = page.locator(".site-header");
  const sidebar = page.locator(".member-sidebar");
  await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeVisible();
  await expect(header.getByRole("link", { name: "About this atlas" })).toHaveCount(0);
  await expect(sidebar).toBeVisible();
  await expect(sidebar.getByRole("link", { name: "Artists", exact: true })).toBeVisible();
  await expect(sidebar.getByRole("link", { name: "Museums", exact: true })).toBeVisible();
  const initialSessionRequests = sessionRequests;
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(1440);
  await page.screenshot({ path: info.outputPath("member-desktop.png") });
  await sidebar.getByRole("link", { name: "Museums", exact: true }).click();
  await expect(page).toHaveURL(/\/museums$/);
  await expect(sidebar.getByRole("link", { name: "Museums", exact: true })).toHaveAttribute("aria-current", "page");
  await page.getByRole("button", { name: "Hide navigation", exact: true }).click();
  await expect(sidebar).toBeHidden();
  await header.getByRole("link", { name: "Your account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Everything is open." })).toBeVisible();
  await expect(sidebar).toBeHidden();
  expect(sessionRequests).toBe(initialSessionRequests);
  await page.getByRole("button", { name: "Show navigation", exact: true }).click();
  await expect(sidebar).toBeVisible();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
});

test("Full view hides member navigation and restores its previous state", async ({ page }) => {
  await page.goto("/?start=1800&end=1900");
  const sidebar = page.locator(".member-sidebar");
  await expect(sidebar).toBeVisible();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(sidebar).toHaveJSProperty("inert", true);
  const box = (await page.locator(".explorer").boundingBox())!;
  expect(box.x).toBe(0); expect(box.width).toBe(1440);
  await page.keyboard.press("Escape");
  await expect(sidebar).toHaveJSProperty("inert", false);
  await expect(sidebar).toBeVisible();
  await page.getByRole("button", { name: "Hide navigation", exact: true }).click();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.getByRole("button", { name: "Exit full view", exact: true }).click();
  await expect(sidebar).toBeHidden();
});

test("member drawer fits small screens and returns keyboard focus", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/about");
  for (const width of [390, 320, 768, 1024]) {
    await page.setViewportSize({ width, height: 844 });
    const open = page.getByRole("button", { name: "Open navigation", exact: true });
    await expect(page.locator(".site-header .account-link")).toBeVisible();
    await expect(page.locator(".member-sidebar")).toBeHidden();
    await open.click();
    const drawer = page.getByRole("dialog", { name: "Explore Artlines", exact: true });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole("link", { name: "Museums", exact: true })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`member-drawer-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(drawer).not.toBeVisible();
    await expect(open).toBeFocused();
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  }
  await page.getByRole("button", { name: "Open navigation", exact: true }).click();
  await page.getByRole("dialog", { name: "Explore Artlines", exact: true }).getByRole("link", { name: "Artists", exact: true }).click();
  await expect(page).toHaveURL(/\/artists$/);
  await expect(page.getByRole("dialog", { name: "Explore Artlines", exact: true })).not.toBeVisible();
});

test("signed-out visitors keep the help link and can use Full view", async ({ page }) => {
  // Browser-only anonymous response; the local API's debug access is unchanged.
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.goto("/");
  await expect(page.locator(".site-header").getByRole("link", { name: "About this atlas" })).toBeVisible();
  await expect(page.locator(".site-header .account-link")).toHaveCount(0);
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
});

test("an expired session removes member navigation when the tab regains focus", async ({ page }) => {
  await page.goto("/about");
  await expect(page.locator(".member-sidebar")).toBeVisible();
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  await expect(page.locator(".site-header .account-link")).toHaveCount(0);
  await expect(page.locator(".site-header").getByRole("link", { name: "About this atlas" })).toBeVisible();
  await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
});
