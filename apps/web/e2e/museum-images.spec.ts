import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function results(page: Page) {
  const response = await page.request.get(`/api/backend/v1/museums/musee-du-louvre/works?${new URL(page.url()).searchParams}`);
  expect(response.ok()).toBe(true);
  const data = await response.json();
  await expect(page.getByRole("region", { name: "Museum artwork results" })).toHaveAttribute("aria-busy", "false");
  const count = new Intl.NumberFormat("en-GB");
  await expect(page.getByRole("status").filter({ hasText: "in this view" })).toContainText(`${count.format(data.total)} works in this view · ${count.format(data.image_count)} with images`);
  return data;
}

test("Louvre opens with images and preserves all catalogue records across pagination", async ({ page }) => {
  await page.goto("/museums/musee-du-louvre");
  const first = await results(page);
  expect(first.total).toBeGreaterThan(first.image_count);
  expect(first.image_count).toBeGreaterThan(13);
  await expect(page.getByRole("combobox", { name: "Sort artworks", exact: true })).toHaveValue("images");
  const cards = page.getByRole("region", { name: "Museum artwork results" });
  await expect(cards.getByRole("button", { name: /^Open / })).toHaveCount(first.items.length);
  await expect.poll(() => cards.locator("img").evaluateAll(images => images.filter(image => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0).length)).toBeGreaterThan(0);
  const pager = page.getByRole("navigation", { name: "Artwork pages above results" });
  await pager.getByRole("button", { name: /Next/ }).click();
  const second = await results(page);
  expect(second.total).toBe(first.total);
  const ids = new Set(first.items.map((work: { id: string }) => work.id));
  expect(second.items.some((work: { id: string }) => ids.has(work.id))).toBe(false);
  // The deployed gallery and the separate directory redesign use different
  // labels for the same image filter; exercise both release shapes.
  await page.getByRole("checkbox", { name: /^(With pictures|With an available image)$/ }).check();
  const filtered = await results(page);
  expect(filtered.total).toBe(first.image_count);
  expect(new URL(page.url()).searchParams.has("cursor")).toBe(false);
  expect(filtered.items.every((work: { media_url: string | null }) => !!work.media_url)).toBe(true);
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  expect((await results(page)).total).toBe(first.total);
});

test("Louvre sort, search and deep-linked artwork keep the same image", async ({ page }) => {
  await page.goto("/museums/musee-du-louvre?q=Sardanapale");
  const data = await results(page);
  const illustrated = data.items.find((work: {media_url:string|null}) => work.media_url);
  expect(illustrated).toBeTruthy();
  await page.getByRole("button", { name: `Open ${illustrated.title}`, exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
  await expect(drawer.getByRole("heading", { name: illustrated.title, exact: true })).toBeVisible();
  await expect(drawer.locator(".artwork-image img")).toHaveAttribute("src", new RegExp(encodeURIComponent(illustrated.media_url)));
  await page.reload();
  await expect(drawer.getByRole("heading", { name: illustrated.title, exact: true })).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByRole("combobox", { name: "Sort artworks", exact: true }).selectOption("year");
  expect((await results(page)).total).toBe(data.total);
});

for (const width of [390, 1440]) {
  test(`Louvre gallery fits ${width}px and is accessible`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/museums/musee-du-louvre?image_only=1");
    await results(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    const audit = await new AxeBuilder({ page }).include("#main-content").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(audit.violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`louvre-${width}.png`) });
  });
}
