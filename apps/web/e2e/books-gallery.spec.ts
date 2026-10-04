import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const width of [1440, 390, 320]) test(`books gallery preserves space and keyboard details at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.goto("/books?top100=false&start=1800&end=1900");
  const cards = page.locator(".library-card");
  await expect(cards).toHaveCount(150);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await expect(page.getByRole("group", { name: "Books display" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Scroll books right" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Book index", exact: true })).toHaveCount(0);
  await cards.first().focus();
  const title = await cards.first().locator("strong").textContent();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog", { name: "Book details", exact: true })).toContainText(title!);
  await page.keyboard.press("Escape");
  await expect(cards.first()).toBeFocused();
  await page.screenshot({ path: info.outputPath(`books-gallery-${width}.png`) });
  if (width === 320) {
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
  }
});

for (const view of ["books", "authors"]) test(`${view} scrolls forward, evicts old cards, and restores earlier pages`, async ({ page }) => {
  await page.goto(`/books?top100=false&view=${view}`);
  const cards = page.locator(".library-card"), strip = page.locator(".library-strip");
  await expect(cards).toHaveCount(150);
  const first = await cards.first().getAttribute("data-entry-id");
  for (const count of [300, 450, 600]) {
    await strip.evaluate(el => { el.scrollLeft = el.scrollWidth; });
    await expect(strip.locator("li[aria-posinset]").last()).toHaveAttribute("aria-posinset", String(count));
    await expect(strip).toHaveAttribute("aria-busy", "false");
  }
  expect(await cards.count()).toBeLessThanOrEqual(450);
  await expect(strip.locator("li[aria-posinset]").first()).toHaveAttribute("aria-posinset", "151");
  const last = cards.last(), title = await last.locator("strong").textContent();
  await last.click();
  await expect(page.getByRole("dialog")).toContainText(title!);
  await page.keyboard.press("Escape");
  await strip.evaluate(el => { el.scrollLeft = 0; });
  await expect(cards.first()).toHaveAttribute("data-entry-id", first!);
  await expect(cards.first()).toBeInViewport();
});

test("incremental failures preserve cards and retry the same page", async ({ page }) => {
  await page.goto("/books?top100=false");
  await expect(page.locator(".library-card")).toHaveCount(150);
  let attempts = 0;
  await page.route("**/api/backend/v1/books?*", route => {
    if (!new URL(route.request().url()).searchParams.has("after")) return route.continue();
    if (++attempts === 1) return route.fulfill({ status: 503, json: { error: { message: "Temporary failure" } } });
    return route.continue();
  });
  await page.locator(".library-strip").evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.getByText("Couldn’t load more books.", { exact: true })).toBeVisible();
  await expect(page.locator(".library-card")).toHaveCount(150);
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.locator(".library-card")).toHaveCount(300);
  expect(attempts).toBe(2);
});

test("selected author portrait has credits, opens books, and survives image failure", async ({ page }, info) => {
  await page.goto("/books?view=authors&q=Tolstoy&top100=false");
  const author = page.getByRole('button', { name: /^Leo Tolstoy,.*Open author details$/ });
  await author.click();
  const drawer = page.getByRole("dialog", { name: "Book author details" });
  const portrait = drawer.locator('.author-portrait img');
  await expect(portrait).toBeVisible();
  await expect.poll(() => portrait.evaluate((el: HTMLImageElement) => el.naturalWidth)).toBeGreaterThan(0);
  await expect(drawer.getByRole("link", { name: "Image source" })).toHaveAttribute("href", /commons.wikimedia.org/);
  await expect(drawer).toContainText("Sergei Prokudin-Gorskii");
  await page.screenshot({ path: info.outputPath("tolstoy-portrait.png") });
  await drawer.getByRole("button", { name: "Show books by this author" }).click();
  await expect(page.getByRole("group", { name: "Books display" }).getByRole("button", { name: "Books", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".book-mark").first()).toBeVisible();
  await page.route("**/images/authors/**", route => route.abort());
  await page.goto("/books?view=authors&q=Tolstoy&top100=false");
  await author.click();
  await expect(drawer.getByRole("img", { name: "Portrait unavailable" })).toBeVisible();
  await expect(drawer).toContainText("Leo Tolstoy");
});
