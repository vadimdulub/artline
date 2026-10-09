import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Member previews use the API's loopback-only debug session, with no database fixtures.
test("Account opens Artists and keeps the panel across collection navigation", async ({ page, request }) => {
  expect((await (await request.get("/api/auth/session")).json()).local_debug).toBe(true);
  let sessionRequests = 0;
  page.on("request", req => { if (req.url().endsWith("/api/auth/session")) sessionRequests++; });
  await page.goto("/");
  const header = page.locator(".site-header");
  const account = header.getByRole("link", { name: "Account", exact: true });
  const panel = page.getByRole("complementary", { name: "Account navigation" });
  await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeVisible();
  await expect(header).not.toContainText("A personal study atlas");
  await expect(panel).toHaveCount(0);
  const initialRequests = sessionRequests;
  await account.click();
  await expect(page).toHaveURL(/\/artists$/);
  await expect(panel.getByRole("link", { name: "Artists", exact: true })).toHaveAttribute("aria-current", "page");
  await panel.getByRole("link", { name: "Museums", exact: true }).click();
  await expect(page).toHaveURL(/\/museums$/);
  await expect(panel.getByRole("link", { name: "Museums", exact: true })).toHaveAttribute("aria-current", "page");
  await expect(panel.getByRole("link", { name: "Artists", exact: true })).toBeVisible();
  await account.click();
  await expect(page).toHaveURL(/\/artists$/);
  await panel.getByRole("button", { name: "Collapse account panel" }).click();
  await expect(panel).toHaveAttribute("data-collapsed", "true");
  await expect(panel.getByRole("navigation")).toBeVisible();
  await account.click();
  await expect(panel.getByRole("navigation")).toBeVisible();
  await panel.getByRole("link", { name: "Your account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Everything is open." })).toBeVisible();
  await expect(panel.getByRole("navigation")).toBeVisible();
  expect(sessionRequests).toBe(initialRequests);
  await header.getByRole("link", { name: "Your account", exact: true }).click();
  await expect(page).toHaveURL(/\/artists$/);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
});

test("the account panel is absent from every public explorer tab", async ({ page }) => {
  await page.goto("/artists");
  const header = page.locator(".site-header");
  const panel = page.getByRole("complementary", { name: "Account navigation" });
  await expect(panel).toBeVisible();
  await panel.getByRole("button", { name: "Collapse account panel" }).click();
  for (const name of ["Painters", "Books", "Events", "All"]) {
    await header.getByRole("link", { name, exact: true }).click();
    await expect(panel).toHaveCount(0);
    await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
    await header.getByRole("link", { name: "Account", exact: true }).click();
    await expect(page).toHaveURL(/\/artists$/);
    await expect(panel.getByRole("navigation")).toBeVisible();
    await expect(panel).toHaveAttribute("data-collapsed", "true");
  }
});

for (const width of [1440, 1024, 768, 390, 320]) {
  test(`persistent account navigation fits ${width}px without covering content`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/artists");
    const panel = page.getByRole("complementary", { name: "Account navigation" });
    const header = page.locator(".site-header");
    await expect(panel.getByRole("link", { name: "Artists", exact: true })).toBeInViewport();
    await expect(header.getByRole("link", { name: "Your account", exact: true })).toBeInViewport();
    await expect(page.locator("body")).toHaveCSS("padding-left", width > 900 ? "208px" : "64px");
    const box = (await panel.boundingBox())!;
    expect((await page.locator("main").boundingBox())!.x).toBeGreaterThanOrEqual(box.width);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
    await page.screenshot({ path: info.outputPath(`account-${width}.png`) });
    await page.evaluate(() => window.scrollTo(0, 500));
    expect((await header.boundingBox())!.y).toBe(0);
    expect((await panel.boundingBox())!.y).toBe((await header.boundingBox())!.height);
    const iconPositions = () => panel.locator("nav a>svg").evaluateAll(icons => icons.map(icon => {
      const { x, y } = icon.getBoundingClientRect();
      return { x, y };
    }));
    const expandedIcons = await iconPositions();
    await panel.getByRole("button", { name: "Collapse account panel" }).click();
    await expect(panel).toHaveAttribute("data-collapsed", "true");
    await expect(panel).toHaveCSS("width", "56px");
    await expect(page.locator("body")).toHaveCSS("padding-left", "56px");
    if (width > 900) expect(await iconPositions()).toEqual(expandedIcons);
    expect((await page.locator("main").boundingBox())!.x).toBeGreaterThanOrEqual(56);
    expect((await panel.boundingBox())!.y).toBe((await header.boundingBox())!.height);
    for (const name of ["Artists", "Museums", "Art history guide", "About & sources", "Your account"]) {
      const link = panel.getByRole("link", { name, exact: true });
      await expect(link).toBeVisible();
      await expect(link).toHaveAttribute("title", name);
      await expect(link.locator("svg")).toBeVisible();
      await expect(link.locator("span")).toBeHidden();
      expect((await link.boundingBox())!.width).toBeGreaterThanOrEqual(44);
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    await panel.getByRole("link", { name: "Museums", exact: true }).focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/\/museums$/);
    await expect(panel).toHaveAttribute("data-collapsed", "true");
    await expect(panel.getByRole("link", { name: "Museums", exact: true })).toHaveAttribute("aria-current", "page");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`account-icons-${width}.png`) });
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await panel.getByRole("button", { name: "Expand account panel" }).click();
    await expect(panel).toHaveAttribute("data-collapsed", "false");
    await expect(panel).toHaveCSS("width", width > 900 ? "208px" : "64px");
    await expect(panel.getByRole("link", { name: "Artists", exact: true }).locator("span")).toBeVisible();
    await expect(panel.getByRole("navigation")).toBeVisible();
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await panel.getByRole("link", { name: "Artists", exact: true }).focus();
    await page.keyboard.press("Escape");
    await expect(panel).toHaveAttribute("data-collapsed", "true");
    await expect(panel.getByRole("navigation")).toBeVisible();
    await expect(header.getByRole("link", { name: "Account", exact: true })).toBeFocused();
  });
}

test("signed-out and expired sessions have no account panel", async ({ page }) => {
  await page.goto("/artists");
  await expect(page.locator(".member-sidebar")).toBeVisible();
  // Browser-only expired-session response; local API access is unchanged.
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.locator(".member-sidebar")).toHaveCount(0);
  const header = page.locator(".site-header");
  await expect(header.getByRole("link", { name: "Account", exact: true })).toHaveAttribute("href", "/account");
  await expect(header.getByRole("link", { name: "About this atlas" })).toBeVisible();
  await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
  await header.getByRole("link", { name: "Account", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sign in with Google" })).toBeVisible();
});

test("the panel remembers its width after reload and respects reduced motion", async ({ page }) => {
  await page.goto("/artists");
  const panel = page.getByRole("complementary", { name: "Account navigation" });
  await panel.getByRole("button", { name: "Collapse account panel" }).click();
  await page.reload();
  await expect(panel).toHaveAttribute("data-collapsed", "true");
  await expect(panel).toHaveCSS("width", "56px");
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(panel).toHaveCSS("transition-duration", "0s");
  await panel.getByRole("button", { name: "Expand account panel" }).click();
  await expect(panel).toHaveCSS("width", "208px");
  await page.reload();
  await expect(panel).toHaveAttribute("data-collapsed", "false");
  await expect(panel).toHaveCSS("width", "208px");
  await page.setViewportSize({ width: 768, height: 360 });
  await expect(panel.getByRole("button", { name: "Collapse account panel" })).toBeInViewport();
  const account = panel.getByRole("link", { name: "Your account", exact: true });
  await account.focus();
  await expect(account).toBeInViewport();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/account$/);
});

test("the panel remains usable when browser storage is unavailable", async ({ page }) => {
  await page.addInitScript(() => {
    const { getItem, setItem } = Storage.prototype;
    Storage.prototype.getItem = function (key) {
      if (key === "artline:account-panel-collapsed") throw new DOMException("Storage unavailable", "SecurityError");
      return getItem.call(this, key);
    };
    Storage.prototype.setItem = function (key, value) {
      if (key === "artline:account-panel-collapsed") throw new DOMException("Storage unavailable", "SecurityError");
      return setItem.call(this, key, value);
    };
  });
  await page.goto("/artists");
  const panel = page.getByRole("complementary", { name: "Account navigation" });
  await panel.getByRole("button", { name: "Collapse account panel" }).click();
  await expect(panel).toHaveCSS("width", "56px");
  await panel.getByRole("link", { name: "Museums", exact: true }).click();
  await expect(page).toHaveURL(/\/museums$/);
  await expect(panel).toHaveAttribute("data-collapsed", "true");
  await panel.getByRole("button", { name: "Expand account panel" }).click();
  await expect(panel).toHaveCSS("width", "208px");
});
