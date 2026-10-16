import { expect, test, type Locator, type Page } from "@playwright/test";

async function settle(page: Page) {
  await page.evaluate(() => new Promise<void>(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
}

async function position(viewer: Locator) {
  return viewer.evaluate(node => {
    const image = node.querySelector(".image-scroll-canvas img")!.getBoundingClientRect();
    const stage = node.querySelector(".image-dialog-stage")!;
    return { x: image.x, y: image.y, width: image.width, height: image.height, panX: stage.scrollLeft, panY: stage.scrollTop, dialogY: node.scrollTop };
  });
}

async function remainsInPlace(page: Page, viewer: Locator, before: Awaited<ReturnType<typeof position>>) {
  await settle(page);
  const after = await position(viewer);
  for (const key of Object.keys(before) as (keyof typeof before)[]) expect(Math.abs(after[key] - before[key]), key).toBeLessThanOrEqual(.5);
}

for (const width of [1440, 390]) {
  test(`copying always-visible colors keeps the painting and zoom steady at ${width}px`, async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/artists/claude-monet?art_images=true");
    await page.locator(".work-card").first().click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    const colors = viewer.getByRole("group", { name: "Artwork colors", exact: true });
    const swatch = colors.getByRole("list", { name: "Dominant image colors" }).getByRole("button").first();
    await expect(swatch).toBeVisible();
    await expect(colors.getByRole("button", { name: "Colors", exact: true })).toHaveCount(0);
    await expect(colors.getByText(/Approximate image colors/)).toHaveCount(0);
    await expect(viewer.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
    expect((await viewer.locator(".image-dialog-stage").boundingBox())!.height).toBeGreaterThan(650);
    for (const color of await colors.getByRole("list").getByRole("button").all()) await expect(color).toBeInViewport();
    await swatch.scrollIntoViewIfNeeded();
    await settle(page);
    const fit = await position(viewer);
    await swatch.click();
    await expect(colors.getByRole("status")).toContainText("copied");
    expect((await colors.getByRole("status").boundingBox())!.y).toBeLessThan(120);
    await remainsInPlace(page, viewer, fit);

    await viewer.getByText("Details", { exact: true }).click();
    await expect(viewer.locator("details[open]")).toBeVisible();
    await remainsInPlace(page, viewer, fit);
    await page.keyboard.press("Escape");
    await expect(viewer.locator("details[open]")).toHaveCount(0);
    await expect(viewer).toBeVisible();
    await remainsInPlace(page, viewer, fit);

    await viewer.getByRole("button", { name: "Zoom in", exact: true }).click();
    await expect(viewer.getByLabel("Image magnification")).toHaveText("1.5× fit");
    await viewer.locator(".image-dialog-stage").evaluate(element => { element.scrollLeft = 31; element.scrollTop = 37; });
    await swatch.scrollIntoViewIfNeeded();
    await settle(page);
    const zoom = await position(viewer);
    await swatch.click();
    await remainsInPlace(page, viewer, zoom);

    await page.evaluate(() => Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: () => Promise.reject(new Error("Clipboard denied")) } }));
    await swatch.click();
    const fallback = colors.getByRole("textbox", { name: "Copy HEX value" });
    await expect(fallback).toBeFocused();
    await remainsInPlace(page, viewer, zoom);
    await page.keyboard.press("Escape");
    await expect(fallback).toHaveCount(0);
    await expect(viewer).toBeVisible();
    await expect(swatch).toBeFocused();
    await remainsInPlace(page, viewer, zoom);
  });
}

for (const width of [1440, 390, 320]) {
  test(`full view preserves room and navigation with long titles at ${width}px`, async ({ page }) => {
    const endpoint = "/api/backend/v1/artists/claude-monet/works";
    const data = await (await page.request.get(`${endpoint}?image_only=true`)).json();
    const [first, second] = data.items;
    const longTitle = "A landscape beside a river with distant houses and changing light, with the complete extended title and descriptive subtitle retained from its museum catalogue";
    const credit = "Museum image credit. ".repeat(20);
    await page.route(`**${endpoint}?*`, async route => {
      const response = await route.fetch();
      const body = await response.json();
      body.items = body.items.map((work: { id: string }) => work.id === second.id ? { ...work, title: longTitle, attribution_text: credit } : work);
      await route.fulfill({ response, json: body });
    });
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/artists/claude-monet?art_images=true");
    const trigger = page.locator(".work-card").first();
    await trigger.click();
    const viewer = page.getByRole("dialog", { name: /Enlarged image:/ });
    await expect(viewer.getByRole("heading")).toHaveText(first.title);
    const next = viewer.getByRole("button", { name: "Next artwork", exact: true });
    const close = viewer.getByRole("button", { name: "Close enlarged image" });
    const beforeNext = await next.boundingBox();
    const beforeClose = await close.boundingBox();
    await next.click();
    await expect(viewer.getByRole("heading")).toHaveText(longTitle);
    expect(await next.boundingBox()).toEqual(beforeNext);
    expect(await close.boundingBox()).toEqual(beforeClose);
    await expect(viewer.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
    await settle(page);
    const image = await position(viewer);
    const stage = (await viewer.locator(".image-dialog-stage").boundingBox())!;
    expect(stage.height).toBeGreaterThan(650);
    expect(Math.min(Math.abs(image.width - stage.width), Math.abs(image.height - stage.height))).toBeLessThan(1);
    expect(await viewer.evaluate(node => node.scrollHeight <= node.clientHeight && node.scrollWidth <= node.clientWidth)).toBe(true);
    await viewer.getByText("Details", { exact: true }).click();
    await expect(viewer.locator("details[open] strong")).toHaveText(longTitle);
    await expect(viewer.locator("details[open] .image-dialog-credit")).toHaveText(credit.trim());
    await remainsInPlace(page, viewer, image);
    await page.keyboard.press("Escape");
    if (width === 390) {
      await page.setViewportSize({ width: 844, height: 390 });
      await settle(page);
      expect((await viewer.locator(".image-dialog-stage").boundingBox())!.height).toBeGreaterThan(250);
      expect(await viewer.evaluate(node => node.scrollHeight <= node.clientHeight)).toBe(true);
    }
    await page.keyboard.press("Escape");
    await expect(viewer).toHaveCount(0);
    await expect(trigger).toBeFocused();
    await page.unrouteAll({ behavior: "wait" });
  });
}
