import { e2eEditorToken } from "./editor-token";
import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("work selection moves keyboard focus into the visible record", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?artist=giotto");
  const drawer = page.locator(".painter-dialog");
  const card = drawer.locator(".work-row").nth(1);
  await card.focus();
  await card.press("Enter");
  const heading = drawer.locator("#artwork-record-title");
  await expect(heading).toBeFocused();
  await expect(heading).toContainText("Kiss of Judas");
  const toolbar = await drawer.locator(".dialog-toolbar").boundingBox();
  expect((await heading.boundingBox())!.y).toBeGreaterThan(toolbar!.y + toolbar!.height);
  await drawer.getByRole("button", { name: "Next work", exact: true }).click();
  await expect(heading).toBeFocused();
  await expect(heading).toContainText("Golden Gate");
  await page.screenshot({ path: "../../docs/screenshots/round2-work-focus-mobile.png" });
  await drawer.getByRole("button", { name: "← Artworks by year", exact: true }).click();
  await expect(drawer.locator(".work-row").nth(2)).toBeFocused();
  await page.goto("/artists/claude-monet");
  await expect(page.locator(".artwork-image img")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Browse selected works" })).toHaveCount(0);
});

test("extra filters dismiss with Escape, Done, outside click and focus leaving", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".timeline-counter")).toContainText("11 painters");
  const filters = page.locator(".more-filters");
  const trigger = filters.locator("summary");
  await trigger.click();
  await expect(filters.locator("select").first()).toBeVisible();
  await filters.locator("select").first().focus();
  await page.keyboard.press("Escape");
  await expect(filters).not.toHaveAttribute("open");
  await expect(trigger).toBeFocused();
  await trigger.click();
  await filters.getByRole("button", { name: "Done", exact: true }).click();
  await expect(trigger).toBeFocused();
  await expect(filters).not.toHaveAttribute("open");
  await trigger.click();
  await page.locator("#timeline-title").click();
  await expect(filters).not.toHaveAttribute("open");
  await trigger.click();
  await filters.getByRole("button", { name: "Done", exact: true }).focus();
  await page.keyboard.press("Tab");
  await expect(filters).not.toHaveAttribute("open");
});

test("range controls normalize edits and give non-drag, filter-preserving recovery", async ({ page }) => {
  await page.goto("/?start=1800&end=1900&q=Monet");
  await expect(page.locator(".timeline-counter")).toContainText("1 painter");
  const start = page.getByLabel("Start year", { exact: true });
  const end = page.getByLabel("End year", { exact: true });
  await start.fill("1800.2");
  await start.press("Enter");
  await expect(start).toHaveValue("1800");
  expect(new URL(page.url()).searchParams.get("start")).toBe("1800");
  await end.fill("");
  await end.press("Enter");
  await expect(end).toHaveValue("1900");
  await page.getByRole("button", { name: "Move range 10 years earlier" }).click();
  await expect(start).toHaveValue("1790");
  await expect(end).toHaveValue("1890");
  await expect(page.getByLabel("Timeline start handle")).toHaveAttribute("aria-valuemax", "1889");
  await expect(page.getByLabel("Timeline end handle")).toHaveAttribute("aria-valuemin", "1791");
  await page.getByRole("searchbox").fill("No such painter");
  await expect(page.getByRole("heading", { name: "No painters in this view" })).toBeVisible();
  await page.getByRole("button", { name: "Remove filters", exact: true }).click();
  await expect(start).toHaveValue("1790");
  await expect(page.getByRole("searchbox")).toHaveValue("");
  await page.getByRole("searchbox").fill("Giotto");
  await page.getByRole("button", { name: "Show full date range" }).click();
  await expect(page.getByRole("searchbox")).toHaveValue("Giotto");
  await expect(start).toHaveValue("1100");
  await expect(page.getByRole("button", { name: "Move range 10 years earlier" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Move range 10 years later" })).toBeDisabled();
});

test("original artwork supports real zoom, scrolling, fit and nested modal focus", async ({ page }) => {
  await page.goto("/?artist=giotto");
  const opener = page.getByRole("button", { name: "View larger" });
  await opener.click();
  const viewer = page.locator(".image-dialog");
  const img = viewer.locator("img");
  const zoomIn = viewer.getByRole("button", { name: "Zoom in", exact: true });
  await expect(zoomIn).toBeEnabled();
  const imageURL = new URL((await img.getAttribute("src"))!, page.url());
  expect(imageURL.origin).toBe(new URL(page.url()).origin);
  expect(imageURL.pathname).toMatch(/^\/assets\//);
  const fit = (await img.boundingBox())!;
  await zoomIn.click();
  await expect(viewer.locator("output")).toHaveText("1.5× fit");
  expect((await img.boundingBox())!.width / fit.width).toBeCloseTo(1.5, 1);
  await page.keyboard.press("+");
  await expect(viewer.locator("output")).toHaveText("2× fit");
  const stage = viewer.getByRole("region", { name: /Image detail:/ });
  await stage.focus();
  await stage.press("ArrowDown");
  await expect.poll(() => stage.evaluate(node => node.scrollTop)).toBeGreaterThan(0);
  await page.screenshot({ path: "../../docs/screenshots/round2-image-zoom-desktop.png" });
  await stage.press("0");
  await expect(viewer.locator("output")).toHaveText("Fit");
  await expect(viewer.getByRole("button", { name: "Zoom out", exact: true })).toBeDisabled();
  expect((await img.boundingBox())!.width).toBeCloseTo(fit.width, 0);
  const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
  expect(scan.violations).toEqual([]);
  await page.keyboard.press("Escape");
  await expect(opener).toBeFocused();
  await expect(page.locator(".painter-dialog")).toBeVisible();
});

test("narrow and short screens retain readable controls and full-viewer access", async ({ page }) => {
  for (const size of [{ width: 320, height: 740 }, { width: 390, height: 844 }, { width: 844, height: 390 }]) {
    await page.setViewportSize(size);
    await page.goto("/");
    await expect(page.locator(".timeline-counter")).toContainText("11 painters");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(size.width);
    if (size.width < 760) {
      expect(await page.getByRole("searchbox").evaluate(node => parseFloat(getComputedStyle(node).fontSize))).toBeGreaterThanOrEqual(16);
      await page.screenshot({ path: `../../docs/screenshots/round2-timeline-${size.width}.png`, fullPage: true });
    }
    await page.goto("/artists/katsushika-hokusai");
    await page.getByRole("button", { name: "View larger" }).click();
    const viewer = page.locator(".image-dialog");
    await expect(viewer.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
    await expect(viewer.getByRole("button", { name: "Close enlarged image" })).toBeInViewport();
    expect(await viewer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(size.width);
    await page.screenshot({ path: `../../docs/screenshots/round2-image-fit-${size.width}.png` });
  }
});

test("copy fallback selects the URL and original-image failures can be retried", async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async () => { throw new Error("Denied for test"); } } }));
  await page.goto("/artists/giotto");
  await page.getByRole("button", { name: "Copy artwork link" }).click();
  const fallback = page.getByLabel("Copy this artwork link");
  await expect(fallback).toBeFocused();
  expect(await fallback.evaluate(node => { const input = node as HTMLInputElement; return input.selectionEnd! - input.selectionStart! === input.value.length; })).toBe(true);
  await page.route("**/assets/artworks/**", route => route.abort());
  await page.getByRole("button", { name: "View larger" }).click();
  await expect(page.getByRole("button", { name: "Retry image" })).toBeVisible();
  await page.unroute("**/assets/artworks/**");
  await page.getByRole("button", { name: "Retry image" }).click();
  await expect(page.getByRole("button", { name: "Zoom in", exact: true })).toBeEnabled();
});

test("catalogue refresh disables stale actions and table can scroll with keyboard", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/catalogue");
  await page.getByLabel("Editor token", { exact: true }).fill(e2eEditorToken());
  const table = page.getByRole("region", { name: "Painter catalogue", exact: true });
  await expect(table).toHaveAttribute("aria-busy", "false");
  await expect(table.getByRole("button", { name: "Edit", exact: true }).first()).toBeEnabled();
  await table.focus();
  await table.press("ArrowRight");
  await expect.poll(() => table.evaluate(node => node.scrollLeft)).toBeGreaterThan(0);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/backend/v1/catalogue/artists?**", async route => { await gate; await route.continue(); });
  await page.getByRole("searchbox", { name: "Search painters" }).fill("Giotto");
  await expect(table).toHaveAttribute("aria-busy", "true");
  await expect(table.getByRole("button", { name: "Edit", exact: true }).first()).toBeDisabled();
  release();
  await expect(table).toHaveAttribute("aria-busy", "false");
  await expect(table.getByRole("button", { name: "Edit", exact: true })).toHaveCount(1);
  await page.screenshot({ path: "../../docs/screenshots/round2-catalogue-mobile.png", fullPage: true });
});
