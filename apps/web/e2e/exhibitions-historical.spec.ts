import { test, expect, type APIRequestContext } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const api = process.env.ARTLINE_HISTORICAL_API_URL;
async function historicalID(request: APIRequestContext) {
  const response = await request.get(`${api}/api/v1/exhibitions?source=royal-academy&start=1769&end=1769&limit=2`);
  expect(response.ok()).toBe(true);
  const data = await response.json();
  expect(data.total).toBe(1);
  return data.items[0].id as string;
}

test.beforeEach(() => test.skip(!api, "Requires the verified historical API URL; no database fixtures"));

test("historical catalogue, source filters and stable paging", async ({ page }) => {
  await page.goto("/exhibitions?source=royal-academy");
  await expect(page.getByRole("heading", { name: "Exhibitions", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "221 exhibitions", exact: true })).toBeVisible();
  await expect(page.getByRole("main").getByText(/1600–1989/)).toBeVisible();
  await expect(page.getByRole("link", { name: /Expanded studies/ })).toHaveCount(0);
  await page.getByRole("searchbox", { name: "Search exhibition titles" }).fill("1769");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page.getByRole("heading", { name: "1 exhibition", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Royal Academy Summer Exhibition 1769", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Royal Academy Summer Exhibition 1769", exact: true })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toHaveCount(0);
});

test("illustrated exhibited works lead and all destinations stay internal", async ({ page, request }) => {
  const id = await historicalID(request);
  const response = await request.get(`${api}/api/v1/exhibitions/${id}/entries?limit=50`);
  expect(response.ok()).toBe(true);
  const first = await response.json();
  expect(first.total).toBeGreaterThanOrEqual(119);
  expect(first.hasMore).toBe(true);
  await page.goto(`/exhibitions/${id}`);
  const works = page.locator('li[id^="work-"]');
  await expect(works).toHaveCount(50);
  for (const index of [0, 1]) {
    const image = works.nth(index).locator("img");
    await expect(image).toBeVisible();
    await expect(image).toHaveJSProperty("complete", true);
    expect(await image.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBeGreaterThan(0);
  }
  await expect(page.locator('main a[href^="https://"],main a[href^="http://"]')).toHaveCount(0);
  const firstIDs = await works.evaluateAll(elements => elements.map(element => element.id));
  await page.getByRole("link", { name: "More artworks →", exact: true }).click();
  await expect(works.first()).not.toHaveAttribute("id", firstIDs[0]);
  await expect(works).toHaveCount(50);
  const secondIDs = await works.evaluateAll(elements => elements.map(element => element.id));
  expect(secondIDs.some(id => firstIDs.includes(id))).toBe(false);
  await page.getByRole("link", { name: "First artwork page", exact: true }).click();
  const exhibitedResponse = await request.get(`${api}/api/v1/exhibitions/${id}/entries?limit=50&participation=exhibited`);
  expect(exhibitedResponse.ok()).toBe(true);
  const exhibited = await exhibitedResponse.json();
  expect(exhibited.total).toBeGreaterThanOrEqual(3);
  await page.getByRole("link", { name: /Recorded as exhibited/ }).click();
  await expect(works).toHaveCount(exhibited.items.length);
  await expect(page.locator('main a[href*="artwork_id=7c8f7ddb-9ab1-56f8-a8df-511013c3256a"]').first()).toBeVisible();
  await expect(page.locator('main a[href^="/artists/"]').first()).toHaveAttribute("href", /\/artists\//);
});

test("historical gallery fits desktop and mobile and keeps account navigation", async ({ page, request }, info) => {
  const id = await historicalID(request);
  await page.goto(`/exhibitions/${id}`);
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440 || width === 390) {
      expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
      await page.screenshot({ path: info.outputPath(`historical-${width}.png`), fullPage: true });
    }
  }
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  const account = page.getByRole("dialog").getByRole("region", { name: "Your account", exact: true });
  await expect(account.getByRole("link", { name: "Exhibitions", exact: true })).toBeVisible();
});

test("public exhibition keeps museum navigation behind sign-in", async ({ page }) => {
  await page.goto("/exhibitions/b2721ff6-def1-5958-a7b3-b634e978f318");
  await expect(page.getByRole("heading", { name: "The Silver Jubilee Exhibition", exact: true })).toBeVisible();
  const museum = page.locator('main a[href^="/museums/"]').first();
  await expect(museum).toBeVisible();
  await museum.click();
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toBeVisible();
  await page.getByRole("button", { name: "Close sign-in window" }).click();
  await expect(museum).toBeFocused();
});
