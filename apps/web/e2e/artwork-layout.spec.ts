import { test, expect, type Locator } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistWorksPage } from "../lib/types";
import type { AtlasResponse } from "../lib/atlas";

const endpoint = "/api/backend/v1/artists/claude-monet/works";

async function arrowPositions(container: Locator) {
  return Promise.all(["Previous artwork", "Next artwork"].map(async name => {
    const button = container.getByRole("button", { name, exact: true });
    await expect(button).toBeInViewport();
    const bounds = (await button.boundingBox())!;
    expect(bounds.width).toBeGreaterThanOrEqual(44);
    expect(bounds.height).toBeGreaterThanOrEqual(44);
    return bounds;
  }));
}

test("a painter without pictures keeps the filter reachable so all records can be opened", async ({ page }) => {
  const data = await (await page.request.get(endpoint)).json() as ArtistWorksPage;
  const work = { ...data.items[0], media_url: null };
  await page.route(`**${endpoint}?*`, async route => {
    const imagesOnly = new URL(route.request().url()).searchParams.get("image_only") === "true";
    await route.fulfill({ json: { ...data, items: imagesOnly ? [] : [work], total: imagesOnly ? 0 : 1, matching_total: imagesOnly ? 0 : 1, next_cursor: "", undated_count: 0, groups: imagesOnly ? [] : [{ year: work.creation_year_start, start_index: 0, count: 1, has_uncertain_dates: true }] } });
  });
  await page.goto("/?artist=claude-monet");
  const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
  await expect(drawer.getByRole("heading", { name: "No artworks with pictures", exact: true })).toBeVisible();
  await drawer.getByRole("checkbox", { name: "With pictures" }).uncheck();
  await expect(drawer.locator(".work-row")).toHaveCount(1);
  await drawer.locator(".work-row").click();
  const panel = drawer.locator(".artwork-panel");
  await expect(panel.locator(".artwork-creator")).toContainText("Claude Monet");
  await expect(panel.locator(".large-placeholder")).toBeVisible();
  await expect(panel.getByRole("heading", { name: work.title, exact: true })).toBeVisible();
  await expect(panel.getByRole("button", { name: /View larger/ })).toHaveCount(0);
});

for (const width of [1440, 390, 320]) {
  test(`All artwork controls stay fixed while the next record loads at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const query = "type=artwork&start=1850&end=1851&highlights=false";
    const response = await page.request.get(`/api/backend/v1/atlas?${query}&limit=2`);
    await expect(response).toBeOK();
    const data = await response.json() as AtlasResponse;
    const [first, second] = data.lanes[0].items;
    let releaseDetail!: () => void;
    const detailGate = new Promise<void>(resolve => { releaseDetail = resolve; });
    await page.route(`**/api/backend/v1/atlas/artworks/${second.id}`, async route => { await detailGate; await route.continue(); });
    await page.goto(`/all?${query}&itemType=artwork&item=${first.id}`);
    const drawer = page.getByRole("dialog", { name: "Artwork details", exact: true });
    await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(first.title);
    const creator = (await drawer.locator(".artwork-creator").boundingBox())!;
    const figure = (await drawer.locator(".artwork-image").boundingBox())!;
    const title = (await drawer.getByRole("heading", { level: 2 }).boundingBox())!;
    expect(creator.y + creator.height).toBeLessThanOrEqual(figure.y);
    expect(figure.y + figure.height).toBeLessThanOrEqual(title.y);
    const before = await arrowPositions(drawer);
    expect(await drawer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    try {
      await drawer.getByRole("button", { name: "Next artwork", exact: true }).click();
      await expect(drawer.getByRole("status").filter({ hasText: "Opening artwork…" })).toBeVisible();
      await expect(drawer.getByRole("button", { name: "Next artwork", exact: true })).toBeDisabled();
      await expectStableArrows(drawer, before);
    } finally { releaseDetail(); }
    await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(second.title);
    await expectStableArrows(drawer, before);
    expect(await drawer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    await drawer.getByRole("button", { name: "Previous artwork", exact: true }).click();
    await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(first.title);
    await expectStableArrows(drawer, before);
    await page.screenshot({ path: info.outputPath(`all-artwork-${width}.png`) });
  });

  test(`museum artwork puts the recorded creator and image before details at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const data = await (await page.request.get(`${endpoint}?image_only=true`)).json() as ArtistWorksPage;
    const work = data.items.find(work => work.holding)!;
    expect(work.holding).toBeTruthy();
    await page.goto(`/museums/${work.holding!.slug}?work=${work.id}`);
    const drawer = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
    const creator = drawer.locator(".artwork-creator");
    await expect(creator).toContainText("Claude Monet");
    const image = drawer.locator(".artwork-image");
    await expect.poll(() => image.locator("img").evaluate(node => (node as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
    expect((await creator.boundingBox())!.y + (await creator.boundingBox())!.height).toBeLessThanOrEqual((await image.boundingBox())!.y);
    expect((await image.boundingBox())!.y + (await image.boundingBox())!.height).toBeLessThanOrEqual((await drawer.getByRole("heading", { name: work.title, exact: true }).boundingBox())!.y);
    expect(await drawer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    const scan = await new AxeBuilder({ page }).include('.painter-dialog[open]').withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`museum-artwork-${width}.png`) });
    await drawer.getByRole("button", { name: /View larger/ }).click();
    const large = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(large.locator(".image-dialog-artist")).toHaveText("Claude Monet");
    if (width === 390) {
      const scan = await new AxeBuilder({ page }).include('.image-dialog[open]').withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
      expect(scan.violations).toEqual([]);
      await page.screenshot({ path: info.outputPath("museum-fullscreen-mobile.png") });
    }
  });
}

async function expectStableArrows(container: Locator, before: Awaited<ReturnType<typeof arrowPositions>>) {
  const after = await arrowPositions(container);
  after.forEach((bounds, index) => {
    expect(Math.abs(bounds.x - before[index].x)).toBeLessThanOrEqual(1);
    expect(Math.abs(bounds.y - before[index].y)).toBeLessThanOrEqual(1);
  });
}

for (const width of [1440, 390, 320]) {
  test(`artwork picture filter defaults on and remembers an explicit opt-out at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?artist=claude-monet");
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    const chronology = drawer.getByRole("region", { name: "Artworks by year", exact: true });
    const filter = chronology.getByRole("checkbox", { name: "With pictures" });
    await expect(filter).toBeChecked();
    await expect(chronology.locator(".work-row")).toHaveCount(24);
    await filter.scrollIntoViewIfNeeded();
    const headingBounds = (await chronology.getByRole("heading", { name: "Artworks by year", exact: true }).boundingBox())!;
    const filterBounds = (await filter.boundingBox())!;
    const yearBounds = (await chronology.getByRole("combobox", { name: "Artwork year" }).boundingBox())!;
    expect(filterBounds.y).toBeGreaterThanOrEqual(headingBounds.y - 12);
    expect(filterBounds.y - headingBounds.y).toBeLessThan(110);
    expect(filterBounds.y + filterBounds.height).toBeLessThan(yearBounds.y);
    await page.screenshot({ path: info.outputPath(`picture-filter-${width}.png`) });

    const request = page.waitForRequest(req => req.url().includes(endpoint + "?") && new URL(req.url()).searchParams.get("image_only") === "false");
    await filter.uncheck();
    await request;
    await expect(page).toHaveURL(/art_images=false/);
    await page.reload();
    await expect(filter).not.toBeChecked();
    const illustratedRequest = page.waitForRequest(req => req.url().includes(endpoint + "?") && new URL(req.url()).searchParams.get("image_only") === "true");
    await filter.check();
    await illustratedRequest;
    await expect(filter).toBeChecked();
    expect(await drawer.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
  });

  test(`artwork identity, image and stable arrows survive long titles at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const data = await (await page.request.get(`${endpoint}?image_only=true`)).json() as ArtistWorksPage;
    const [first, second] = data.items;
    // Change only browser responses: exercise very different caption heights without editing catalogue data.
    const longTitle = "An unusually long catalogue title describing a landscape, its river, distant houses and changing light, with a second descriptive subtitle retained from the museum record";
    await page.route(`**${endpoint}?*`, async route => {
      const response = await route.fetch();
      const body = await response.json() as ArtistWorksPage;
      body.items = body.items.map(work => work.id === second.id ? { ...work, title: longTitle, attribution_text: "Museum image credit. ".repeat(20) } : work);
      await route.fulfill({ response, json: body });
    });
    await page.goto("/?artist=claude-monet&art_images=true");
    const drawer = page.getByRole("dialog", { name: "Painter details", exact: true });
    await drawer.locator(".work-row").first().click();
    const panel = drawer.locator(".artwork-panel");
    const creator = panel.locator(".artwork-creator");
    await expect(creator).toContainText("Claude Monet");
    const figure = panel.locator(".artwork-image");
    await expect.poll(() => figure.locator("img").evaluate(node => (node as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
    const creatorBounds = (await creator.boundingBox())!;
    const figureBounds = (await figure.boundingBox())!;
    const titleBounds = (await panel.getByRole("heading", { name: first.title, exact: true }).boundingBox())!;
    expect(creatorBounds.y + creatorBounds.height).toBeLessThanOrEqual(figureBounds.y);
    expect(figureBounds.y + figureBounds.height).toBeLessThanOrEqual(titleBounds.y);

    // Navigate after the user has scrolled, not only at the automatic opening position.
    await drawer.evaluate(node => { node.scrollTop += 32; });
    const normalBefore = await arrowPositions(panel);
    const scrollBefore = await drawer.evaluate(node => node.scrollTop);
    await panel.getByRole("button", { name: "Next artwork", exact: true }).click();
    await expect(panel.getByRole("heading", { name: longTitle, exact: true })).toBeVisible();
    await expectStableArrows(panel, normalBefore);
    expect(await drawer.evaluate(node => node.scrollTop)).toBeCloseTo(scrollBefore, 0);
    await page.screenshot({ path: info.outputPath(`artwork-panel-${width}.png`) });
    await panel.getByRole("button", { name: "Previous artwork", exact: true }).click();
    await expect(panel.getByRole("heading", { name: first.title, exact: true })).toBeVisible();
    await expectStableArrows(panel, normalBefore);

    await panel.getByRole("button", { name: /View larger/ }).click();
    const large = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(large.locator(".image-dialog-artist")).toContainText("Claude Monet");
    const largeBefore = await arrowPositions(large);
    const closeBefore = (await large.getByRole("button", { name: "Close enlarged image" }).boundingBox())!;
    await large.getByRole("button", { name: "Next artwork", exact: true }).click();
    await expect(large.getByRole("heading")).toHaveText(longTitle);
    await expectStableArrows(large, largeBefore);
    expect(await large.getByRole("button", { name: "Close enlarged image" }).boundingBox()).toEqual(closeBefore);
    expect(await large.evaluate(node => node.scrollWidth <= node.clientWidth)).toBe(true);
    expect(await large.evaluate(node => node.scrollHeight <= node.clientHeight)).toBe(true);
    await expect(large.getByRole("button", { name: "Zoom in" })).toBeEnabled();
    await large.getByRole("button", { name: "Zoom in" }).click();
    await expect(large.getByLabel("Image magnification")).toHaveText("1.5× fit");
    await expectStableArrows(large, largeBefore);
    await page.screenshot({ path: info.outputPath(`artwork-fullscreen-${width}.png`) });
    await large.getByRole("button", { name: "Previous artwork", exact: true }).press("Enter");
    await expect(large.getByRole("heading")).toHaveText(first.title);
    await expect(large.getByLabel("Image magnification")).toHaveText("Fit");
    await expectStableArrows(large, largeBefore);
    if (width === 390) {
      await page.setViewportSize({ width: 844, height: 390 });
      const landscapeBefore = await arrowPositions(large);
      await large.getByRole("button", { name: "Next artwork", exact: true }).click();
      await expect(large.getByRole("heading")).toHaveText(longTitle);
      await expectStableArrows(large, landscapeBefore);
      expect(await large.evaluate(node => node.scrollHeight <= node.clientHeight)).toBe(true);
      expect((await large.locator(".image-dialog-stage").boundingBox())!.height).toBeGreaterThan(100);
      await page.screenshot({ path: info.outputPath("artwork-fullscreen-landscape.png") });
    }
    await page.keyboard.press("Escape");
    await expect(large).toHaveCount(0);
    await expect(panel.getByRole("button", { name: /View larger/ })).toBeFocused();
  });
}
