import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function settled(page: import("@playwright/test").Page, count?: number) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(count === undefined ? /books in this view/ : `${count.toLocaleString("en-GB")} books in this view`);
}

for (const width of [1440, 390, 320]) {
  test(`crowded Books offer working filters at ${width}px`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/books?top100=false&start=1950&end=1959");
    await settled(page);
    const column = page.locator(".period-column");
    await expect(column).toHaveCount(1);
    await expect(page.locator(".density-help")).toContainText("Many books overlap these years");
    const label = (await column.getAttribute("aria-label"))!;
    const count = Number(label.match(/, (\d+) books$/)![1]);
    expect(count).toBeGreaterThan(0); expect(count).toBeLessThanOrEqual(100);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`books-crowded-${width}.png`) });
    if (width === 320) {
      await page.locator(".density-actions").getByRole("button", { name: label, exact: true }).focus();
      await page.keyboard.press("Enter");
    } else await column.click();
    await settled(page, count);
    await expect(page.locator(".book-mark")).toHaveCount(count);
    expect(new URL(page.url()).searchParams.get("start")).toBe("1950");
    expect(new URL(page.url()).searchParams.get("end")).toBe("1959");
    if (width <= 760) await page.getByRole("button", { name: "Filters", exact: true }).click();
    await expect(page.getByRole("checkbox", { name: "Top 100 books", exact: true })).not.toBeChecked();
    if (width <= 760) await page.getByRole("button", { name: "Close filters", exact: true }).click();
    await page.reload(); await settled(page, count);
    await page.goBack(); await settled(page);
    await expect(page.locator(".density-help")).toBeVisible();
    await page.goForward(); await settled(page, count);
    await page.locator(".book-mark").first().click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
  });
}

test("Russian-language books drill through periods and authors without losing filters", async ({ page }, testInfo) => {
  await page.goto("/books?top100=false"); await settled(page, 8685);
  await page.locator('summary[aria-label^="Languages:"]').click();
  await page.getByRole("checkbox", { name: "Russian", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  const russian=await (await page.request.get("/api/backend/v1/books?language=Q7737&limit=1")).json();
  await settled(page, russian.total);
  await page.getByRole("button", { name: /^Explore 1850–1899,/ }).click();
  await settled(page, 206);
  await page.screenshot({ path: testInfo.outputPath("russian-books-suggestions.png") });
  await expect(page.getByRole("button", { name: "Filter by Author: Leo Tolstoy, 33 books", exact: true })).toBeVisible();
  await page.getByRole("button", { name: /^Explore 1880–1889,/ }).click();
  await settled(page, 89);
  await expect(page.locator(".book-mark")).toHaveCount(89);
  expect(new URL(page.url()).searchParams.get("language")).toBe("Q7737");
  await page.goto("/books?top100=false&language=Q7737&start=1850&end=1899"); await settled(page, 206);
  await page.getByRole("button", { name: "Filter by Author: Leo Tolstoy, 33 books", exact: true }).click();
  await settled(page, 33);
  const params = new URL(page.url()).searchParams;
  expect(params.get("language")).toBe("Q7737"); expect(params.get("author")).toBe("Leo Tolstoy");
  expect(params.get("start")).toBe("1850"); expect(params.get("end")).toBe("1899");
  await expect(page.locator(".book-mark")).toHaveCount(33);
  await page.reload(); await settled(page, 33);
  await page.getByRole("button", { name: "Remove Author: Leo Tolstoy filter", exact: true }).click();
  await settled(page, 206);
  await page.getByRole("button", { name: "Show Top 100 books", exact: true }).click();
  await settled(page);
  await expect(page.getByRole("checkbox", { name: "Top 100 books", exact: true })).toBeChecked();
  expect(new URL(page.url()).searchParams.get("language")).toBe("Q7737");
  expect(new URL(page.url()).searchParams.get("start")).toBe("1850");
});
