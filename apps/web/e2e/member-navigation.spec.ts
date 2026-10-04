import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Member previews use the real API's loopback-only debug session. No database fixtures.
test("Account opens the menu only on request and keeps the shared session", async ({ page, request }, info) => {
  const session = await (await request.get("/api/auth/session")).json();
  expect(session.local_debug).toBe(true);
  let sessionRequests = 0;
  page.on("request", req => { if (req.url().endsWith("/api/auth/session")) sessionRequests++; });
  await page.goto("/about");
  const header = page.locator(".site-header");
  const account = header.getByRole("button", { name: "Account", exact: true });
  const sidebar = page.locator(".member-sidebar");
  await expect(account).toHaveAttribute("aria-expanded", "false");
  await expect(sidebar).toBeHidden();
  await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
  await expect(header.getByRole("link", { name: "Your account", exact: true })).toHaveCount(0);
  const initialSessionRequests = sessionRequests;
  await account.click();
  await expect(account).toHaveAttribute("aria-expanded", "true");
  await expect(sidebar.getByRole("link", { name: "Artists", exact: true })).toBeVisible();
  await expect(sidebar.getByRole("link", { name: "Museums", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBe(1440);
  await page.screenshot({ path: info.outputPath("member-desktop.png") });
  await sidebar.getByRole("link", { name: "Museums", exact: true }).click();
  await expect(page).toHaveURL(/\/museums$/);
  await expect(sidebar).toBeHidden();
  await account.click();
  await expect(sidebar.getByRole("link", { name: "Museums", exact: true })).toHaveAttribute("aria-current", "page");
  await account.click();
  await expect(sidebar).toBeHidden();
  await account.click();
  await sidebar.getByRole("link", { name: "Your account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Everything is open." })).toBeVisible();
  await expect(sidebar).toBeHidden();
  expect(sessionRequests).toBe(initialSessionRequests);
  await account.click();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await sidebar.getByRole("link", { name: "Artists", exact: true }).focus();
  await page.keyboard.press("Escape");
  await expect(sidebar).toBeHidden();
  await expect(account).toBeFocused();
});

test("Full view hides member navigation and restores its previous state", async ({ page }) => {
  await page.goto("/?start=1800&end=1900");
  const sidebar = page.locator(".member-sidebar");
  await expect(sidebar).toBeHidden();
  await page.getByRole("button", { name: "Account", exact: true }).click();
  await expect(sidebar).toBeVisible();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(sidebar).toHaveJSProperty("inert", true);
  const box = (await page.locator(".explorer").boundingBox())!;
  expect(box.x).toBe(0); expect(box.width).toBe(1440);
  await page.keyboard.press("Escape");
  await expect(sidebar).toHaveJSProperty("inert", false);
  await expect(sidebar).toBeVisible();
  await page.getByRole("button", { name: "Account", exact: true }).click();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.getByRole("button", { name: "Exit full view", exact: true }).click();
  await expect(sidebar).toBeHidden();
});

test("member drawer fits small screens and returns keyboard focus", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/about");
  for (const width of [390, 320, 768, 1024]) {
    await page.setViewportSize({ width, height: 844 });
    const open = page.getByRole("button", { name: "Account", exact: true });
    await expect(open).toBeVisible();
    await expect(open).toHaveAttribute("aria-expanded", "false");
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
  await page.getByRole("button", { name: "Account", exact: true }).click();
  await page.getByRole("dialog", { name: "Explore Artlines", exact: true }).getByRole("link", { name: "Artists", exact: true }).click();
  await expect(page).toHaveURL(/\/artists$/);
  await expect(page.getByRole("dialog", { name: "Explore Artlines", exact: true })).not.toBeVisible();
});

test("signed-out visitors keep the help link and can use Full view", async ({ page }) => {
  // Browser-only anonymous response; the local API's debug access is unchanged.
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.goto("/");
  await expect(page.locator(".site-header").getByRole("link", { name: "About this atlas" })).toBeVisible();
  await expect(page.locator(".site-header").getByRole("link", { name: "Account", exact: true })).toBeVisible();
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
});

test("an expired session removes member navigation when the tab regains focus", async ({ page }) => {
  await page.goto("/about");
  await page.getByRole("button", { name: "Account", exact: true }).click();
  await expect(page.locator(".member-sidebar")).toBeVisible();
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  await expect(page.locator(".site-header").getByRole("link", { name: "Account", exact: true })).toBeVisible();
  await expect(page.locator(".site-header").getByRole("link", { name: "About this atlas" })).toBeVisible();
  await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
});


test("header stays at the top and the menu closes across desktop and mobile", async ({ page }, info) => {
  await page.goto("/about");
  const header = page.locator(".site-header");
  const account = header.getByRole("button", { name: "Account", exact: true });
  const drawer = page.getByRole("dialog", { name: "Explore Artlines", exact: true });
  for (const width of [1440, 800, 768, 761, 760, 621, 620, 390, 320]) {
    await page.setViewportSize({ width, height: 600 });
    await page.evaluate(() => window.scrollTo(0, 500));
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(0);
    await expect.poll(async () => (await header.boundingBox())?.y).toBe(0);
    await expect(account).toBeInViewport();
    const logo = (await header.locator(".wordmark-logo").boundingBox())!;
    const navigation = (await header.locator(".primary-nav").boundingBox())!;
    expect(logo.x < navigation.x + navigation.width && logo.x + logo.width > navigation.x && logo.y < navigation.y + navigation.height && logo.y + logo.height > navigation.y).toBe(false);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`sticky-header-${width}.png`) });
  }
  await account.click();
  await expect(drawer).toBeVisible();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await expect(drawer).toBeHidden();
  await expect(account).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".member-sidebar")).toBeHidden();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  await account.click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(account).toHaveAttribute("aria-expanded", "false");
  await expect(drawer).toBeHidden();
});
