import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mockBooks } from "./books-fixture";

test.beforeEach(async ({ page }) => { await mockBooks(page); });

test("book drawer matches the right panel on desktop and fills the phone screen", async ({ page }, testInfo) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books?q=Homer");
    const opener = page.getByRole("button", { name: /^The Odyssey, Homer,/ });
    await expect(opener).toBeVisible();
    const before = await page.locator(".timeline-dark").boundingBox();
    await opener.click();
    const drawer = page.getByRole("dialog", { name: "Book details", exact: true });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
    await expect(drawer.getByRole("heading", { name: "About this book" })).toBeVisible();
    await expect(drawer).toContainText("A long return becomes a meditation on memory");
    await expect(drawer).toContainText("Homecoming · identity");
    await expect(drawer).toContainText("c. 8th century BCE");
    const box = (await drawer.boundingBox())!;
    expect(box.x + box.width).toBeCloseTo(width, 0);
    expect(box.height).toBeCloseTo(900, 0);
    if (width > 760) expect(box.x).toBeGreaterThan(width / 2);
    else expect(box.x).toBe(0);
    expect(await drawer.evaluate(el => el.scrollWidth)).toBeLessThanOrEqual(box.width + 1);
    expect(await page.evaluate(() => document.body.style.overflow)).toBe("hidden");
    const close = drawer.getByRole("button", { name: "Close book details" });
    await close.focus();
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Tab");
      expect(await drawer.evaluate(el => el.contains(document.activeElement))).toBe(true);
    }
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`book-panel-${width}.png`) });
    await expect(drawer.getByRole("button", { name: "Next book" })).toBeDisabled();
    await drawer.getByRole("button", { name: "Previous book" }).click();
    await expect(drawer.getByRole("heading", { name: "The Iliad", exact: true })).toBeVisible();
    await expect(drawer.getByRole("button", { name: "Previous book" })).toBeDisabled();
    await drawer.getByRole("button", { name: "Next book" }).click();
    await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(drawer).toHaveCount(0);
    await expect(opener).toBeFocused();
    expect(await page.locator(".timeline-dark").boundingBox()).toEqual(before);
    expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
    await expect(page.getByLabel("Find a book or author")).toHaveValue("Homer");
  }
});

test("title clicks open the same panel and browser history restores the selection", async ({ page }) => {
  await page.goto("/books");
  const cover = page.getByRole("button", { name: "Open Being and Nothingness by Jean-Paul Sartre", exact: true });
  await cover.scrollIntoViewIfNeeded();
  const scroll = await page.evaluate(() => window.scrollY);
  await cover.click();
  const drawer = page.getByRole("dialog", { name: "Book details" });
  await expect(drawer.getByRole("heading", { name: "Being and Nothingness", exact: true })).toBeVisible();
  await expect(drawer.getByRole("heading", { name: "About the creator", exact: true })).toBeVisible();
  await expect(drawer).toContainText("Born 1905 · Died 1980");
  expect(new URL(page.url()).searchParams.get("book")).toBe("being-nothingness");
  await page.goBack();
  await expect(drawer).toHaveCount(0);
  await expect(cover).toBeFocused();
  expect(await page.evaluate(() => window.scrollY)).toBe(scroll);
  await page.goForward();
  await expect(drawer.getByRole("heading", { name: "Being and Nothingness", exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Close book details" }).click();
  await expect(drawer).toHaveCount(0);
  await expect(cover).toBeFocused();
  await page.locator("#book-being-nothingness").getByRole("button").click();
  await expect(drawer).toBeVisible();
  await page.mouse.click(10, 150);
  await expect(drawer).toHaveCount(0);
});

test("linked book details survive reload outside the active list filters", async ({ page }) => {
  await page.goto("/books?q=Sartre&start=1900&end=2000&book=odyssey");
  const drawer = page.getByRole("dialog", { name: "Book details" });
  await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Next book" })).toBeDisabled();
  await page.reload();
  await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Close book details" }).click();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  await expect(page.getByLabel("Find a book or author")).toHaveValue("Sartre");
  await expect(page.getByLabel("Book start year")).toHaveValue("1900");
  await expect(page.getByLabel("Book end year")).toHaveValue("2000");
  expect(new URL(page.url()).searchParams.has("book")).toBe(false);
});

test("book detail failures recover and unknown books remain closable", async ({ page }) => {
  await page.route("**/api/backend/v1/books/odyssey", route => route.fulfill({ status: 503, json: { error: { message: "Book temporarily unavailable." } } }));
  await page.goto("/books?q=Sartre&book=odyssey");
  const drawer = page.getByRole("dialog", { name: "Book details" });
  await expect(drawer.getByRole("alert")).toContainText("Book temporarily unavailable.");
  await page.unroute("**/api/backend/v1/books/odyssey");
  await drawer.getByRole("button", { name: "Retry book" }).click();
  await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
  await page.goto("/books?book=missing");
  await expect(drawer.getByRole("alert")).toContainText("This book is not in the current selection.");
  await drawer.getByRole("button", { name: "Close book details" }).click();
  await expect(drawer).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
});

test("ArtWorks keeps its painter drawer with the shared frame", async ({ page }) => {
  await page.goto("/?q=Monet");
  const painter = page.locator(".artist-mark").first();
  await expect(painter).toBeVisible();
  await painter.click();
  const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "Close painter details" })).toBeInViewport();
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(painter).toBeFocused();
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
});
