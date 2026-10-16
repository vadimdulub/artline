import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("public exhibition search, source evidence and museum access", async ({ page }) => {
  await page.goto("/exhibitions?source=cleveland&q=Picasso+and+Paper");
  await expect(page.getByRole("heading", { name: "Exhibitions", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Picasso and Paper", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Picasso and Paper", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Documented artworks", exact: true })).toBeVisible();
  await expect(page.locator("main img").first()).toBeVisible();
  await page.getByText("Sources and record evidence", { exact: true }).click();
  await expect(page.locator("details[open] a").first()).toHaveAttribute("href", /^https:\/\//);
  const museum = page.locator('main a[href^="/museums/"]').first();
  await expect(museum).toBeVisible(); await museum.click();
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toBeVisible();
  await page.getByRole("button", { name: "Close sign-in window" }).click();
  await expect(museum).toBeFocused();
});

test("bounded filters, paging, responsive layout and accessibility", async ({ page }, info) => {
  await page.goto("/exhibitions?source=moma");
  await page.getByRole("searchbox", { name: "Search exhibition titles" }).fill("Picasso");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page).toHaveURL(/q=Picasso/);
  await expect(page.getByRole("heading", { level: 3 }).first()).toContainText(/Picasso/i);
  await page.getByRole("button", { name: "Remove Title: Picasso filter" }).click();
  await expect(page).not.toHaveURL(/q=/);
  await page.getByRole("link", { name: "Next exhibitions" }).click();
  await expect(page).toHaveURL(/after=/);
  await expect(page.getByRole("link", { name: "First page", exact: true })).toBeVisible();
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440 || width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`exhibitions-${width}.png`) });
  }
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await expect(page.getByRole("searchbox", { name: "Search exhibition titles" })).toBeVisible();
  await page.getByRole("searchbox", { name: "Search exhibition titles" }).fill("Picasso");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page).toHaveURL(/q=Picasso/);
});

test("real exhibition entry pages have no overlap and validate filters", async ({ request }) => {
  const list = await request.get("/api/backend/v1/exhibitions?source=cleveland&limit=100&state=held");
  expect(list.status()).toBe(200);
  const exhibition = (await list.json()).items.find((item: { entryCount: number }) => item.entryCount > 50);
  expect(exhibition).toBeTruthy();
  const url = `/api/backend/v1/exhibitions/${exhibition.id}/entries?limit=10`;
  const first = await (await request.get(url)).json();
  expect(first.items).toHaveLength(10); expect(first.hasMore).toBe(true);
  const second = await (await request.get(`${url}&after=${first.nextCursor}`)).json();
  expect(second.items).toHaveLength(10);
  expect(first.items.some((a: { id: string }) => second.items.some((b: { id: string }) => a.id === b.id))).toBe(false);
  expect((await request.get("/api/backend/v1/exhibitions?start=2000&end=1800")).status()).toBe(400);
  expect((await request.get("/api/backend/v1/exhibitions?after=invalid")).status()).toBe(400);
});

test("exhibition pages fit the existing ephemeral member sidebar", async ({ page, request }) => {
  test.skip(!process.env.ARTLINE_EXHIBITIONS_DEBUG_SESSION_URL, "Requires an existing loopback-only local-debug API");
  const session = await (await request.get(process.env.ARTLINE_EXHIBITIONS_DEBUG_SESSION_URL!)).json();
  expect(session.local_debug).toBe(true);
  // Use the API's actual ephemeral debug response for this browser only.
  // The exhibition API stays read-only; no account/session fixtures are stored.
  await page.route("**/api/auth/session", route => route.fulfill({ json: session }));
  await page.goto("/exhibitions?source=cleveland&q=Picasso");
  const panel = page.getByRole("complementary", { name: "Account navigation" });
  await expect(panel).toBeVisible();
  for (const width of [1440, 1024, 768]) {
    await page.setViewportSize({ width, height: 900 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const sidebar = await panel.boundingBox();
    expect((await page.locator("main").boundingBox())!.x).toBeGreaterThanOrEqual(sidebar!.width);
    await expect(panel.getByRole("link", { name: "Exhibitions", exact: true })).toHaveAttribute("aria-current", "page");
  }
});
