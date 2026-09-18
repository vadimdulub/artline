import { expect, test } from "@playwright/test";

// Release checks do not submit forms, create fixtures or modify the catalogue.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/**", route => {
    if (route.request().method() !== "GET") return route.abort("blockedbyclient");
    return route.continue();
  });
});

test("women artists filter is available in production", async ({ page }) => {
  await page.goto("/?women=true&popular=false");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.getByRole("checkbox", { name: "Women artists", exact: true })).toBeChecked();
  await expect(page.getByRole("checkbox", { name: "Top 100 painters", exact: true })).not.toBeChecked();
  await expect(page.locator(".timeline-counter")).toContainText("535 painters");
  await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link"))
    .toHaveText(["Painters", "Books", "Events", "All"]);
});

test("book catalogue and sourced event description are delivered", async ({ page }) => {
  await page.goto("/books?top100=false");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText("8,685 books");
  await page.goto("/events?event=event-q361");
  const panel = page.getByRole("dialog", { name: "Event details" });
  await expect(panel.getByRole("heading", { name: "First World War", exact: true })).toBeVisible();
  await expect(panel.locator('section[aria-labelledby="event-about"] p')).toContainText("global conflict between two coalitions");
  await expect(panel.getByRole("link", { name: "CC BY-SA 4.0", exact: true })).toBeVisible();
});

for (const width of [1440, 390]) {
  test(`unified atlas renders all three bounded lanes at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/all");
    await page.getByRole("button", { name: "The First World War", exact: true }).click();
    await expect(page.locator(".all-explorer .timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toHaveCount(0);
    await expect(page.locator(".all-lane>header h2")).toHaveText(["Artworks", "Books", "Events"]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`atlas-${width}.png`) });
  });
}

test("selected real book cover loads with its source credit", async ({ page }, info) => {
  await page.goto("/books?book=odyssey");
  const panel = page.getByRole("dialog", { name: "Book details" });
  const image = panel.getByRole("img");
  await expect(image).toBeVisible();
  await expect.poll(() => image.evaluate(node => {
    const image = node as HTMLImageElement;
    return image.complete && image.naturalWidth > 100;
  }), { timeout: 25000 }).toBe(true);
  await expect(panel.getByRole("link", { name: "Image source", exact: true }))
    .toHaveAttribute("href", /^https:\/\/commons.wikimedia.org\/wiki\/File:/);
  await page.screenshot({ path: info.outputPath("book-cover.png") });
});

test("latest UI keeps year controls responsive while a read is pending", async ({ page }) => {
  await page.goto("/all?selection=true&type=book&start=1700&end=1900");
  const stage = page.locator(".all-explorer .timeline-stage");
  await expect(stage).toHaveAttribute("aria-busy", "false");
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/backend/v1/atlas?*", async route => {
    await pending;
    await route.continue().catch(() => {});
  });
  try {
    await page.getByRole("button", { name: "Move range 1 year later", exact: true }).click();
    await expect(page.getByLabel("All start year", { exact: true })).toHaveValue("1701", { timeout: 1000 });
    await expect(page.locator(".all-canvas-heading .loading-spinner")).toBeVisible();
    await page.getByRole("button", { name: "Move range 1 year later", exact: true }).click();
    await expect(page.getByLabel("All start year", { exact: true })).toHaveValue("1702", { timeout: 1000 });
  } finally {
    release();
  }
  await expect(stage).toHaveAttribute("aria-busy", "false");
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toHaveCount(0);
  await expect(page.getByLabel("All start year", { exact: true })).toHaveValue("1702");
  await page.unrouteAll({ behavior: "wait" });
});
