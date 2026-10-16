import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("local exhibition collection, account navigation and source coverage", async ({ page }, info) => {
  await page.goto("/exhibitions");
  await expect(page.getByRole("heading", { level: 1, name: "Exhibitions" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Exhibitions" })).toHaveCount(0);
  await expect(page.getByRole("complementary", { name: "Account navigation" }).getByRole("link", { name: "Exhibitions" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Expanded studies 700/ })).toBeVisible();
  await expect(page.locator("main img").first()).toBeVisible();
  await expect.poll(() => page.locator("main img").first().evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
  await expect(page.locator('main a[href^="http"], main a[href^="//"]')).toHaveCount(0);
  await expect(page.locator('main a[aria-label^="View artworks in"]')).toHaveCount(40);
  for (const width of [1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440 || width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`directory-${width}.png`) });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator('main a[aria-label^="View artworks in"]').first().scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath("exhibition-pictures-1440.png") });
  await page.setViewportSize({ width: 320, height: 1000 });
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  await expect(page.getByRole("region", { name: "Your account" }).getByRole("link", { name: "Exhibitions" })).toBeVisible();
  await page.getByRole("button", { name: "Close menu" }).click();
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.getByRole("link", { name: "Entire archive", exact: true }).click();
  await expect(page).toHaveURL(/collection=archive/);
  await expect(page.getByRole("heading", { name: /108,\d{3} exhibitions/ })).toBeVisible();
});

test("expanded study shows complete entries, source ideas, artist histories and related shows", async ({ page }, info) => {
  await page.goto("/exhibitions?q=ABSTRACTION+IN+ART");
  await page.getByRole("heading", { level: 3 }).first().getByRole("link").click();
  await expect(page.getByRole("heading", { name: "About the exhibition" })).toBeVisible();
  await expect(page.getByText(/of \d+ public listings/)).toBeVisible();
  await expect(page.locator('main a[href^="http"], main a[href^="//"]')).toHaveCount(0);
  await expect(page.locator('main a[href*="theme="]').first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Artworks in the exhibition" })).toBeVisible();
  const gallery = page.getByRole("region", { name: "Artworks in the exhibition" });
  await expect.poll(() => gallery.locator("img").count()).toBeGreaterThan(0);
  await expect.poll(() => gallery.locator("img").first().evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
  expect(await gallery.evaluate(element => Boolean(element.compareDocumentPosition(document.querySelector("#overview")!) & Node.DOCUMENT_POSITION_FOLLOWING))).toBe(true);
  await expect(page.getByRole("link", { name: "Exhibition history", exact: true }).first()).toBeVisible();
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440 || width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`study-${width}.png`) });
  }
  await page.locator('main a[href*="theme="]').first().click();
  await expect(page).toHaveURL(/theme=/);
  await expect(page.getByRole("heading", { level: 3 }).first()).toBeVisible();
});

test("museum study remains public and preserves sign-in return for museum destinations", async ({ page }) => {
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null, local_debug: false } }));
  await page.goto("/exhibitions/cf8a5362-6ba5-5d02-9337-ee235a700cd2");
  await expect(page.getByRole("heading", { name: "Picasso and Paper", exact: true })).toBeVisible();
  await expect(page.getByText(/partial exhibition checklist/)).toBeVisible();
  const museum = page.locator('main a[href^="/museums/"]').first();
  await museum.click();
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toBeVisible();
  await page.getByRole("button", { name: "Close sign-in window" }).click();
  await expect(museum).toBeFocused();
});

test("exhibited works open local artwork pages and link back to the exact exhibition", async ({ page }, info) => {
  await page.goto("/exhibitions/71ff8e00-4566-5c73-834b-eeb9f8cc5033");
  await page.getByRole("navigation", { name: "Artwork evidence" }).getByRole("link", { name: "Recorded as exhibited 47" }).click();
  await expect(page).toHaveURL(/participation=exhibited/);
  const work = page.locator('main h3 a[href^="/exhibitions/artworks/"]').first();
  const title = await work.innerText();
  await work.click();
  await expect(page).toHaveURL(/\/exhibitions\/artworks\/[a-f0-9-]+$/);
  await expect(page.getByRole("heading", { level: 1, name: title, exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Exhibition history", exact: true })).toBeVisible();
  await expect(page.getByText("Recorded as exhibited", { exact: true })).toBeVisible();
  await expect(page.locator('main a[href^="http"], main a[href^="//"]')).toHaveCount(0);
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width === 1440 || width === 390) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`artwork-${width}.png`), fullPage: true });
  }
  await page.getByRole("heading", { level: 3, name: "Stephen Antonakos: Project Drawings, 1967-73" }).getByRole("link").click();
  await expect(page.getByRole("heading", { level: 1, name: "Stephen Antonakos: Project Drawings, 1967-73" })).toBeVisible();
});

test("exhibition images and navigation stay in our catalogue", async ({ page }) => {
  const requests: string[] = [];
  page.on("request", request => { if (request.resourceType() === "image") requests.push(request.url()); });
  await page.goto("/exhibitions/71ff8e00-4566-5c73-834b-eeb9f8cc5033");
  const gallery = page.getByRole("region", { name: "Artworks in the exhibition" });
  await expect(gallery.locator("img")).toHaveCount(47);
  await expect(page.locator('main a[href^="http"], main a[href^="//"]')).toHaveCount(0);
  const first = gallery.locator("figure a").first();
  await expect(first).toHaveAttribute("href", /^\/exhibitions\/artworks\//);
  const expectedTitle = await first.locator("img").getAttribute("alt");
  await expect.poll(() => first.locator("img").evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
  await first.click();
  await expect(page.getByRole("heading", { level: 1, name: expectedTitle!, exact: true })).toBeVisible();
  await expect(page.locator("main figure img")).toHaveAttribute("src", /^\/assets\/artworks\//);
  await expect(page.locator('main a[href^="http"], main a[href^="//"]')).toHaveCount(0);
  expect(requests.length).toBeGreaterThan(0);
  expect(requests.every(url => new URL(url).origin === new URL(page.url()).origin)).toBe(true);
});

test("one source artwork retains all four exhibition connections", async ({ page }) => {
  await page.goto("/exhibitions/artworks/26d15c6c-431c-5aa7-b234-7b60b85516ea");
  await expect(page.getByRole("heading", { level: 1, name: "Le Lagon (Lagoon)" })).toBeVisible();
  const history = page.getByRole("region", { name: "Exhibition history" });
  await expect(history.getByRole("listitem")).toHaveCount(4);
  await expect(history.getByText("Listed in exhibition", { exact: false })).toHaveCount(4);
  await expect(page.getByRole("link", { name: "Henri Matisse", exact: true })).toHaveAttribute("href", "/artists/henri-matisse-q5589");
  const links = await history.locator('h3 a[href^="/exhibitions/"]').evaluateAll(nodes => nodes.map(node => node.getAttribute("href")));
  expect(new Set(links).size).toBe(4);
});

test("museum artwork keeps its image, caption, creator and exhibition evidence", async ({ page }, info) => {
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null, local_debug: false } }));
  await page.goto("/exhibitions/cf8a5362-6ba5-5d02-9337-ee235a700cd2");
  await page.getByRole("heading", { name: "Head of a Woman: Madeleine", exact: true }).getByRole("link").click();
  await expect(page).toHaveURL(/\/exhibitions\/artworks\//);
  await expect.poll(() => page.locator("main figure img").evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
  await expect(page.getByText("1905, printed 1913", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Pablo Picasso", exact: true })).toHaveAttribute("href", "/artists/pablo-picasso-q5593");
  await expect(page.getByText(/museum’s object record explicitly links/)).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Sign in to Artline" })).toHaveCount(0);
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`museum-artwork-${width}.png`), fullPage: true });
  }
});
