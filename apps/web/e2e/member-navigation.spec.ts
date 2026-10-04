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
  await panel.getByRole("button", { name: "Hide account panel" }).click();
  await expect(panel.getByRole("navigation")).toBeHidden();
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
  for (const name of ["Painters", "Books", "Events", "All"]) {
    await header.getByRole("link", { name, exact: true }).click();
    await expect(panel).toHaveCount(0);
    await expect(page.locator("body")).toHaveCSS("padding-left", "0px");
    await header.getByRole("link", { name: "Account", exact: true }).click();
    await expect(page).toHaveURL(/\/artists$/);
    await expect(panel.getByRole("navigation")).toBeVisible();
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
    const box = (await panel.boundingBox())!;
    expect((await page.locator("main").boundingBox())!.x).toBeGreaterThanOrEqual(box.width);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
    await page.screenshot({ path: info.outputPath(`account-${width}.png`) });
    await page.evaluate(() => window.scrollTo(0, 500));
    expect((await header.boundingBox())!.y).toBe(0);
    expect((await panel.boundingBox())!.y).toBe((await header.boundingBox())!.height);
    await panel.getByRole("button", { name: "Hide account panel" }).click();
    await expect(panel.getByRole("navigation")).toBeHidden();
    await panel.getByRole("button", { name: "Show account panel" }).click();
    await expect(panel.getByRole("navigation")).toBeVisible();
    if (width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await panel.getByRole("link", { name: "Artists", exact: true }).focus();
    await page.keyboard.press("Escape");
    await expect(panel.getByRole("navigation")).toBeHidden();
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
