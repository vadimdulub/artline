import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function settled(page: import("@playwright/test").Page) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(/painters? in this view/);
}

for (const width of [1440, 1366, 390, 320]) {
  test(`crowded columns lead to filters and an individual painter at ${width}px`, async ({ page }, testInfo) => {
    const height = width === 1366 ? 768 : 1000;
    await page.setViewportSize({ width, height });
    await page.goto("/");
    await settled(page);
    await page.getByRole("checkbox", { name: "Only popular painters" }).uncheck();
    await settled(page);
    for (const name of [/^Explore 1900–1949,/, /^Explore 1900–1909,/]) {
      const period = page.getByRole("button", { name });
      const count = Number((await period.locator(".period-count").innerText()).replaceAll(",", ""));
      await period.click();
      await settled(page);
      await expect(page.locator(".timeline-counter")).toContainText(`${count} painters in this view`);
    }
    const column = page.locator(".period-column");
    await expect(column).toHaveCount(1);
    await expect(column).toBeEnabled();
    await expect(page.locator(".density-help")).toContainText("Many painters overlap these years");
    await expect(column).toHaveCSS("cursor", "pointer");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if (width > 760) {
      const bounds = (await page.locator(".timeline-dark").boundingBox())!;
      expect(bounds.y + bounds.height).toBeLessThanOrEqual(height + 1);
    }
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`crowded-${width}.png`), fullPage: true });
    const suggestionLabel = (await column.getAttribute("aria-label"))!;
    const expectedCount = Number(suggestionLabel.match(/, (\d+) painters$/)![1]);
    expect(expectedCount).toBeGreaterThan(0);
    expect(expectedCount).toBeLessThanOrEqual(300);
    const before = new URL(page.url());
    if (width === 320) {
      await page.locator(".density-results button").focus();
      await page.keyboard.press("Enter");
    } else if (width === 390) {
      await page.locator(".density-actions").getByRole("button", { name: suggestionLabel, exact: true }).click();
    } else await column.click();
    await settled(page);
    const after = new URL(page.url());
    expect(after.searchParams.get("start")).toBe(before.searchParams.get("start"));
    expect(after.searchParams.get("end")).toBe(before.searchParams.get("end"));
    expect(after.searchParams.has("country") || after.searchParams.has("movement")).toBe(true);
    await expect(page.locator(".timeline-counter")).toContainText(`${expectedCount} painters in this view`);
    await expect(page.locator(".artist-mark")).toHaveCount(expectedCount);
    await expect(page.getByRole("checkbox", { name: "Only popular painters" })).not.toBeChecked();
    await page.locator(".artist-mark").first().click();
    await expect(page.getByRole("dialog", { name: "Painter details", exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await page.reload();
    await settled(page);
    await expect(page.locator(".artist-mark")).toHaveCount(expectedCount);
  });
}

test("popular shortcut keeps the crowded period and survives reload", async ({ page }) => {
  await page.goto("/?popular=false&start=1900&end=1909");
  await settled(page);
  await page.getByRole("button", { name: "Show popular painters", exact: true }).click();
  await settled(page);
  await expect(page.getByRole("checkbox", { name: "Only popular painters" })).toBeChecked();
  expect(new URL(page.url()).searchParams.get("start")).toBe("1900");
  expect(new URL(page.url()).searchParams.get("end")).toBe("1909");
  await expect(page.locator(".artist-mark").first()).toBeVisible();
  await page.reload();
  await settled(page);
  await expect(page.getByRole("checkbox", { name: "Only popular painters" })).toBeChecked();
  await page.goBack();
  await settled(page);
  await expect(page.getByRole("checkbox", { name: "Only popular painters" })).not.toBeChecked();
  await expect(page.locator(".period-column")).toBeEnabled();
});
