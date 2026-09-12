import { e2eEditorToken } from "./editor-token";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("dense long-name fixture stays legible and inside timeline bounds", async ({ page, request }) => {
  const seed = await (await request.get("/api/backend/v1/timeline?start=1100&end=2000")).json();
  const items = Array.from({ length: 28 }, (_, i) => ({
    ...seed.items[i % seed.items.length], id: "fixture-" + i, slug: "fixture-" + i,
    name: i > 23 ? "Painter with a very long name " + i : seed.items[i % seed.items.length].name,
    start_year: 1200 + i * 27, end_year: Math.min(2000, 1270 + i * 27), date_display: "c. " + (1200 + i * 27) + "–" + Math.min(2000, 1270 + i * 27)
  }));
  await page.route("**/api/backend/v1/timeline?**", route => route.fulfill({ json: { ...seed, items, total: 28 } }));
  await page.goto("/");
  await expect(page.locator(".artist-mark")).toHaveCount(28);
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 1000 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const bounds = await page.locator(".timeline-stage").boundingBox();
    const labels = await page.locator(".artist-mark>span").evaluateAll(nodes => nodes.map(n => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, bottom: r.bottom }; }));
    for (const [i, a] of labels.entries()) {
      expect(a.x).toBeGreaterThanOrEqual(bounds!.x - 1);
      expect(a.right).toBeLessThanOrEqual(bounds!.x + bounds!.width + 1);
      for (const b of labels.slice(i + 1)) expect(a.bottom <= b.y || b.bottom <= a.y || a.right <= b.x || b.right <= a.x).toBe(true);
    }
    await page.locator(".timeline-dark").screenshot({ path: "../../docs/screenshots/timeline-dense-fixture-" + width + ".png" });
  }
});

test("search shortcut and removable filters preserve the chosen dates", async ({ page }) => {
  await page.goto("/?start=1800&end=1950");
  await expect(page.locator(".timeline-counter")).toContainText("painters");
  await page.keyboard.press("/");
  await expect(page.getByRole("searchbox")).toBeFocused();
  await page.getByRole("searchbox").fill("Monet");
  await expect(page.locator(".timeline-counter")).toContainText("1 painter");
  await page.getByRole("button", { name: "Remove Search: Monet filter" }).click();
  await expect(page.getByRole("searchbox")).toHaveValue("");
  await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1800");
  await expect(page.getByLabel("End year", { exact: true })).toHaveValue("1950");
});

test("painter navigation, nested image viewer, sharing and focus restoration", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  const opener = page.locator(".artist-mark").first();
  await opener.click();
  const drawer = page.getByRole("dialog", { name: "Painter details" });
  await expect(drawer.getByRole("heading", { name: "Giotto di Bondone" })).toBeVisible();
  await drawer.getByRole("button", { name: "Next painter", exact: true }).click();
  await expect(drawer.getByRole("heading", { name: "Jan van Eyck", exact: true })).toBeVisible();
  await drawer.getByRole("button", { name: "Previous painter", exact: true }).click();
  await expect(drawer.getByRole("heading", { name: "Giotto di Bondone" })).toBeVisible();
  await drawer.locator(".work-row").nth(1).click();
  await drawer.getByRole("button", { name: "View larger" }).click();
  const image = page.getByRole("dialog", { name: /Enlarged image:/ });
  await expect(image).toBeVisible();
  await expect(image.locator("img")).toHaveJSProperty("complete", true);
  const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  expect(scan.violations).toEqual([]);
  await page.screenshot({ path: "../../docs/screenshots/artwork-enlarged.png" });
  await page.keyboard.press("Escape");
  await expect(image).toHaveCount(0);
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "View larger" })).toBeFocused();
  await drawer.getByRole("button", { name: "Copy artwork link" }).click();
  await expect(drawer.getByRole("button", { name: "Link copied" })).toBeVisible();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain("/artists/giotto/works/");
  await drawer.getByRole("button", { name: "← Artworks by year", exact: true }).click();
  await expect(drawer.locator(".work-row").nth(1)).toBeFocused();
  await expect(drawer.locator(".work-row").nth(1)).toBeInViewport();
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);
  await expect(opener).toBeFocused();
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
  await opener.click();
  await drawer.getByRole("button", { name: "View larger" }).click();
  await expect(image).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(await page.evaluate(() => document.body.style.overflow)).not.toBe("hidden");
});

test("all seeded painters have a real, accessible local artwork record", async ({ page, request }) => {
  const timeline = await (await request.get("/api/backend/v1/timeline?start=1100&end=2000")).json();
  expect(timeline.items).toHaveLength(11);
  let count = 0;
  for (const painter of timeline.items) {
    const response = await request.get("/api/backend/v1/artists/" + painter.slug);
    expect(response.ok()).toBe(true);
    const record = await response.json();
    expect(record.artworks.length).toBeGreaterThan(0);
    for (const work of record.artworks) {
      count++;
      expect(work.media_url).toMatch(/^\/assets\/artworks\//);
      expect(work.alt_text.length).toBeGreaterThan(20);
      expect(work.citations.length).toBeGreaterThan(0);
      expect(work.status).toBe("review");
      expect((await request.get(work.media_url)).ok()).toBe(true);
    }
    await page.goto("/artists/" + painter.slug);
    await expect.poll(() => page.locator(".artwork-image>img").evaluate(image => (image as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
    await expect(page.locator(".artwork-details")).toContainText("Image rights");
  }
  expect(count).toBe(15);
});

test("major pages and the painter panel pass automated accessibility checks", async ({ page }) => {
  test.setTimeout(90000);
  for (const path of ["/", "/artists/giotto", "/catalogue", "/coverage", "/imports", "/about"]) {
    await page.goto(path);
    if (path === "/") await expect(page.locator(".timeline-counter")).toContainText("11 painters");
    if (path === "/catalogue") await expect(page.getByRole("link", { name: "Giotto di Bondone" })).toBeVisible();
    if (path === "/coverage") await expect(page.locator(".coverage-grid a")).toHaveCount(4);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(results.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })) })), path).toEqual([]);
    for (const width of [320, 390, 768, 1024, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), { message: path + " at " + width }).toBe(true);
    }
    await page.screenshot({ path: "../../docs/screenshots/review-" + (path === "/" ? "timeline" : path.replaceAll("/", "-")) + ".png", fullPage: true });
  }
  await page.goto("/?artist=giotto");
  await expect(page.getByRole("heading", { name: "Giotto di Bondone" })).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  expect(results.violations).toEqual([]);
});

test("failed images and timeline requests recover without stale interactions", async ({ page }) => {
  await page.route("**/_next/image?**", route => route.abort());
  await page.goto("/artists/giotto");
  await expect(page.locator(".artwork-image")).toContainText("Image unavailable");
  await expect(page.getByRole("button", { name: "View larger" })).toHaveCount(0);
  await expect(page.locator(".artwork-details h3")).toContainText("Lamentation");
  await page.unroute("**/_next/image?**");
  await page.goto("/");
  await expect(page.locator(".timeline-counter")).toContainText("11 painters");
  await page.route("**/api/backend/v1/timeline?**", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: { message: "Test connection interrupted" } }) }));
  await page.getByRole("searchbox").fill("Giotto");
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toBeVisible();
  await expect(page.locator(".artist-results button")).toHaveCount(0);
  await page.unroute("**/api/backend/v1/timeline?**");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("1 painter");
});

test("unsaved editor changes are protected and status navigation is shared", async ({ page }) => {
  await page.goto("/catalogue");
  await expect(page.getByRole("heading", { name: "Read-only preview" })).toBeVisible();
  await page.getByLabel("Editor token", { exact: true }).fill(e2eEditorToken());
  const row = page.getByRole("row").filter({ has: page.getByRole("link", { name: "Giotto di Bondone" }) });
  await row.getByRole("button", { name: "Edit", exact: true }).click();
  await expect(page.getByLabel("Display name", { exact: true })).toBeFocused();
  await page.getByLabel("Display name", { exact: true }).fill("Unsaved local test");
  await expect(page.locator(".form-heading")).toContainText("Unsaved changes");
  page.once("dialog", dialog => dialog.dismiss());
  await page.getByRole("link", { name: "Coverage", exact: true }).first().click();
  await expect(page.getByLabel("Display name", { exact: true })).toHaveValue("Unsaved local test");
  page.once("dialog", dialog => dialog.accept());
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await page.getByRole("link", { name: "Coverage", exact: true }).first().click();
  await page.locator(".coverage-grid a").filter({ hasText: "In review" }).click();
  await expect(page.getByRole("combobox", { name: "Status", exact: true })).toHaveValue("review");
});
