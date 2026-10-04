import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Read-only checks against the local catalogue; no fixtures or database writes.
for (const route of ["/", "/books", "/events", "/all"]) {
  test(`full view keeps ${route} inside the viewport across mobile and desktop`, async ({ page }, info) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(route);
    const frame = page.locator(".explorer");
    await page.getByRole("button", { name: "Full view", exact: true }).click();
    await expect(frame).toHaveAttribute("role", "dialog");
    await expect(page.locator(".site-header")).toHaveJSProperty("inert", true);
    await expect(page.getByRole("searchbox").first()).toBeHidden();
    for (const size of [{ width: 390, height: 844 }, { width: 320, height: 568 }, { width: 740, height: 390 }, { width: 1440, height: 1000 }]) {
      await page.setViewportSize(size);
      await expect.poll(async () => (await frame.boundingBox())?.height).toBe(size.height);
      expect((await frame.boundingBox())?.y).toBe(0);
      const exit = page.getByRole("button", { name: "Exit full view", exact: true });
      await expect(exit).toBeInViewport();
      expect((await exit.boundingBox())!.height).toBeGreaterThanOrEqual(44);
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(size.width);
      await page.screenshot({ path: info.outputPath(`full-${size.width}.png`) });
    }
    await page.getByRole("button", { name: "Exit full view", exact: true }).click();
    await expect(frame).toHaveAttribute("data-full-view", "false");
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
    await expect(page.locator(".site-header")).toHaveJSProperty("inert", false);
    await expect(page.getByRole("button", { name: "Full view", exact: true })).toBeVisible();
    await expect(page.getByRole("searchbox").first()).toBeVisible();
  });
}

test("full view preserves filters, keyboard focus, and nested book details", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/books");
  const book = page.locator(".books-undated button").first();
  await expect(book).toBeVisible();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await book.click();
  await expect(page.getByRole("dialog", { name: "Book details", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(book).toBeFocused();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");

  await page.getByRole("button", { name: "Filters", exact: true }).click();
  const women = page.getByRole("checkbox", { name: "Women authors", exact: true });
  await women.check();
  await expect(page).toHaveURL(/women=true/);
  await women.press("Escape");
  await expect(women).toBeHidden();
  await expect(page.getByRole("button", { name: "Filters", exact: true })).toBeFocused();
  await page.keyboard.press("/");
  await expect(page.getByRole("searchbox", { name: "Find a book or author" })).toBeFocused();
  await expect(women).toBeChecked();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Full view", exact: true })).toBeFocused();
  await expect(page).toHaveURL(/women=true/);
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await expect(women).toBeChecked();
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
});

test("full view enlarges paintings and returns from artwork details", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?view=paintings&painter=claude-monet&popular=false&start=1800&end=1950");
  const artwork = page.locator(".all-artwork-card").first();
  await expect(artwork).toBeVisible();
  const before = (await artwork.locator(".all-artwork-image").boundingBox())!.height;
  const url = page.url();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  expect((await artwork.locator(".all-artwork-image").boundingBox())!.height).toBeGreaterThan(before);
  await expect.poll(() => artwork.locator("img").first().evaluate((image: HTMLImageElement) => image.naturalWidth), { timeout: 20000 }).toBeGreaterThan(0);
  await page.screenshot({ path: info.outputPath("paintings-full.png") });
  await artwork.click();
  await expect(page.getByRole("dialog", { name: "Artwork details", exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(artwork).toBeFocused();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Exit full view", exact: true }).click();
  await expect(page).toHaveURL(url);
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});

test("index links leave full view and focus the requested index", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/events");
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.getByRole("link", { name: "Event index", exact: true }).click();
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "false");
  await expect(page.getByRole("heading", { name: "Event index", exact: true })).toBeFocused();
  await expect(page.getByRole("heading", { name: "Event index", exact: true })).toBeInViewport();
  await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
});

test("All keeps full view when closing nested popovers and filter choices", async ({ page }, info) => {
  test.setTimeout(60000);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/all");
  await expect(page.locator(".all-start-card").first()).toBeVisible();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.locator(".all-start-card").first().click();
  await expect(page.locator(".all-artwork-card").first()).toBeVisible({ timeout: 20000 });
  await expect(page.locator(".all-lane")).toHaveCount(3);
  await page.screenshot({ path: info.outputPath("all-populated.png") });
  const details = page.locator(".all-view-context");
  await details.locator("summary").click();
  await page.keyboard.press("Escape");
  await expect(details).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await page.locator(".all-period-filter summary").click();
  expect((await page.locator(".all-period-filter summary").boundingBox())!.height).toBeLessThan(80);
  await expect(page.getByRole("searchbox", { name: "Search period or theme" })).toBeInViewport();
  await page.screenshot({ path: info.outputPath("all-filters.png") });
  await page.keyboard.press("Escape");
  await expect(page.locator(".all-period-filter details")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Filters", exact: true })).toHaveAttribute("aria-expanded", "true");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Filters", exact: true })).toHaveAttribute("aria-expanded", "false");
});
