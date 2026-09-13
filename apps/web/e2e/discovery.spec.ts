import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function settled(page: import("@playwright/test").Page) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(/painters? in this view/);
}

test("popular discovery is the default, opt-out survives reload/back, reset restores it", async ({ page }) => {
  await page.goto("/");
  await settled(page);
  const toggle = page.getByRole("checkbox", { name: "Only popular painters" });
  await expect(toggle).toBeChecked();
  const popular = await (await page.request.get("/api/backend/v1/timeline")).json();
  const all = await (await page.request.get("/api/backend/v1/timeline?popular=false")).json();
  expect(popular.popular_only).toBe(true);
  expect(popular.total).toBeGreaterThan(0);
  expect(all.total).toBeGreaterThan(popular.total);
  expect(popular.items.some((p: { name: string }) => p.name === "Diego Velázquez")).toBe(true);
  await toggle.uncheck();
  await expect(page).toHaveURL(/popular=false/);
  await settled(page);
  await expect(page.locator(".timeline-counter")).toContainText(`${all.total} painters`);
  await page.reload();
  await expect(toggle).not.toBeChecked();
  await settled(page);
  expect(await page.locator(".density-results li").count()).toBe(all.periods.length);
  expect(all.periods.length).toBeLessThanOrEqual(91);
  // Overlapping lifetimes can appear in several periods; totals are unique painters.
  expect(all.periods.every((p: { count: number }) => p.count > 0 && p.count <= all.total)).toBe(true);
  await page.goBack();
  await expect(toggle).toBeChecked();
  await settled(page);
  await toggle.uncheck();
  await page.locator(".reset-button").click();
  await expect(toggle).toBeChecked();
  await settled(page);
});

test("popular scope combines with regions, search and genuine clear-all", async ({ page }) => {
  await page.goto("/?q=Diego%20Vel%C3%A1zquez");
  await settled(page);
  await expect(page.locator(".timeline-counter")).toContainText("1 painter in this view");
  const regions = page.locator(".multi-filter").filter({ has: page.locator('summary[aria-label^="Regions:"]') });
  await regions.locator("summary").click();
  await regions.getByRole("checkbox", { name: "Southern Europe", exact: true }).check();
  await regions.getByRole("checkbox", { name: "Eastern Asia", exact: true }).check();
  await regions.getByRole("button", { name: "Done", exact: true }).click();
  await settled(page);
  await expect(page.locator(".timeline-counter")).toContainText("1 painter in this view");
  await page.reload();
  await settled(page);
  expect(new URL(page.url()).searchParams.getAll("region")).toHaveLength(2);
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Only popular painters" })).not.toBeChecked();
  await expect(page.getByRole("searchbox")).toHaveValue("");
  await settled(page);
});

test("Prado masterpieces connect Velázquez chronology to the museum and image viewer", async ({ page }) => {
  await page.goto("/?q=Diego%20Vel%C3%A1zquez");
  await settled(page);
  const painter = page.locator(".artist-mark").filter({ hasText: "Diego Velázquez" });
  await painter.click();
  const panel = page.getByRole("dialog", { name: "Painter details", exact: true });
  await expect(panel.getByRole("heading", { name: "Diego Velázquez", exact: true })).toBeVisible();
  const work = panel.getByRole("button", { name: /1656 Las Meninas/ });
  await expect(work).toBeVisible();
  expect((await panel.boundingBox())!.x).toBeGreaterThan(0);
  const prado = panel.getByRole("navigation", { name: "Collections for these artworks" }).getByRole("link", { name: "Museo Nacional del Prado", exact: true });
  await expect(prado).toHaveAttribute("href", /museo-del-prado\?artist=diego-velazquez-q297/);
  await panel.getByRole("combobox", { name: "Artwork year" }).selectOption("1656");
  // The catalogue can gain more works from the same year.
  const yearGroup = panel.getByRole("region", { name: "Artworks grouped at 1656", exact: true });
  await expect(yearGroup).toBeVisible();
  await expect(panel.getByRole("region", { name: /^Artworks grouped at / })).toHaveCount(1);
  await expect(yearGroup.getByRole("button", { name: /1656 Las Meninas/ })).toBeVisible();
  await work.click();
  await panel.getByRole("button", { name: "View larger", exact: false }).click();
  await expect(page.locator(".image-dialog")).toBeVisible();
  await expect(page.locator(".image-dialog img")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(panel.getByRole("button", { name: "View larger", exact: false })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(painter).toBeFocused();
  await painter.click();
  await prado.click();
  await expect(page.getByRole("heading", { name: "Museo Nacional del Prado", exact: true })).toBeVisible();
  await expect(page.locator('summary[aria-label="Painters: Diego Velázquez"]')).toBeVisible();
  await expect(page.getByRole("button", { name: "Open Las Meninas", exact: true })).toBeVisible();
  await expect(page.getByText("Madrid, Spain", { exact: true })).toBeVisible();
});

test("discovery and the right panel fit desktop and phones and pass accessibility checks", async ({ page }, testInfo) => {
  for (const { width, height } of [{ width: 1440, height: 1000 }, { width: 1366, height: 768 }, { width: 390, height: 1000 }, { width: 320, height: 1000 }]) {
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await settled(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width > 760) {
      const timeline = (await page.locator(".timeline-dark").boundingBox())!;
      expect(timeline.y + timeline.height).toBeLessThanOrEqual(height + 1);
      await expect(page.locator(".movement-key")).toBeInViewport();
    } else {
      expect((await page.locator(".timeline-lanes").boundingBox())!.height).toBeLessThanOrEqual(350);
    }
    const axis = await page.locator(".tick-row>span").first().boundingBox();
    const mark = await page.locator(".artist-mark").first().boundingBox();
    expect(mark!.y).toBeGreaterThan(axis!.y + 16);
    let scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`popular-after-${width}.png`), fullPage: true });
    await page.getByRole("searchbox").fill("Diego Velázquez");
    await settled(page);
    await page.locator(".artist-mark").filter({ hasText: "Diego Velázquez" }).click();
    const panel = page.getByRole("dialog", { name: "Painter details", exact: true });
    await expect(panel.getByRole("button", { name: /1656 Las Meninas/ })).toBeVisible();
    expect(await panel.evaluate(el => el.scrollWidth)).toBeLessThanOrEqual(width);
    scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`velazquez-prado-${width}.png`) });
  }
});

test("empty searches explain missing coverage and can be cleared with the keyboard", async ({ page }) => {
  await page.goto("/?q=not-a-real-painter-xyz");
  await settled(page);
  await expect(page.getByRole("heading", { name: "No painters in this view" })).toBeVisible();
  await page.getByRole("button", { name: "Remove filters", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("searchbox")).toBeFocused();
  await settled(page);
  await expect(page.locator(".density-results li").first()).toBeVisible();
});

test("failed discovery requests recover without losing the popular preference", async ({ page }) => {
  let fail = true;
  await page.route("**/api/backend/v1/timeline?**", route => fail ? route.fulfill({ status: 503, json: { error: { message: "Temporary test outage" } } }) : route.continue());
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toBeVisible();
  fail = false;
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await settled(page);
  await expect(page.getByRole("checkbox", { name: "Only popular painters" })).toBeChecked();
  await expect(page.locator(".artist-mark").first()).toBeVisible();
});
