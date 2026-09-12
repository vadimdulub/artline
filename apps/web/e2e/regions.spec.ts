import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("regions combine with OR, survive drawer history and reload, and remove individually", async ({ page }) => {
  await page.goto("/?start=1700&end=2000&status=draft");
  await expect(page.locator(".timeline-counter")).toContainText("6 painters");
  await expect.poll(() => new URL(page.url()).searchParams.has("status")).toBe(false);
  const filter = page.locator(".multi-filter");
  await filter.locator("summary").click();
  await filter.getByRole("checkbox", { name: "Northern Europe", exact: true }).check();
  await filter.getByRole("checkbox", { name: "Eastern Asia", exact: true }).check();
  await expect(filter.locator("summary")).toHaveAccessibleName("Regions: 2 selected");
  await expect(page.locator(".timeline-counter")).toContainText("5 painters");
  expect(new URL(page.url()).searchParams.getAll("region")).toEqual(["eastern-asia", "northern-europe"]);
  await filter.getByRole("button", { name: "Done", exact: true }).click();
  await page.locator(".artist-mark").first().click();
  await expect(page.locator(".painter-dialog")).toBeVisible();
  await page.goBack();
  await expect(page.locator(".painter-dialog")).toHaveCount(0);
  await expect(page.locator(".timeline-counter")).toContainText("5 painters");
  await page.reload();
  await expect(page.locator(".timeline-counter")).toContainText("5 painters");
  await page.getByRole("button", { name: "Remove Eastern Asia filter", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("4 painters");
  await expect(page.getByRole("searchbox")).toBeFocused();
  expect(new URL(page.url()).searchParams.getAll("region")).toEqual(["northern-europe"]);
  await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1700");
});

test("other filters intersect regions; clearing regions preserves country, dates and search", async ({ page, request }) => {
  await page.goto("/?start=1700&end=1900&region=northern-europe,eastern-asia&country=JP&q=Hokusai");
  await expect(page.locator(".timeline-counter")).toContainText("1 painter");
  const filter = page.locator(".multi-filter");
  await filter.locator("summary").click();
  await expect(filter.getByRole("checkbox", { name: "Eastern Asia", exact: true })).toBeChecked();
  await expect(filter.getByRole("checkbox", { name: "Northern Europe", exact: true })).toBeChecked();
  await filter.getByRole("button", { name: "Clear regions", exact: true }).click();
  await expect(filter.locator("summary")).toHaveAccessibleName("Regions: All regions");
  const params = new URL(page.url()).searchParams;
  expect(params.has("region")).toBe(false);
  expect(params.get("start")).toBe("1700");
  expect(params.get("end")).toBe("1900");
  expect(params.get("country")).toBe("JP");
  expect(params.get("q")).toBe("Hokusai");
  await filter.getByRole("button", { name: "Done", exact: true }).click();
  await page.locator(".more-filters summary").click();
  await expect(page.getByRole("combobox", { name: "Record status", exact: true })).toHaveCount(0);
  await expect(page.locator(".more-filters select")).toHaveCount(2);
  const restricted = await request.get("http://localhost:8080/api/v1/timeline?region=northern-europe&region=eastern-asia&status=review");
  expect(restricted.status()).toBe(401);
  const publicResult = await request.get("http://localhost:8080/api/v1/timeline?region=northern-europe&region=eastern-asia");
  expect(publicResult.ok()).toBe(true);
  expect((await publicResult.json()).total).toBe(0);
});

test("region menu supports keyboard, Escape, outside click, focus exit and narrow screens", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.locator(".timeline-counter")).toContainText("11 painters");
    const filter = page.locator(".multi-filter");
    const trigger = filter.locator("summary");
    await trigger.focus();
    await trigger.press("Enter");
    const checkbox = filter.getByRole("checkbox", { name: "Eastern Asia", exact: true });
    await checkbox.focus();
    await checkbox.press("Space");
    await expect(checkbox).toBeChecked();
    await expect(filter).toHaveAttribute("open");
    await expect(page.locator(".timeline-counter")).toContainText("1 painter");
    const bounds = (await filter.locator(".multi-filter-panel").boundingBox())!;
    expect(bounds.x).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: `../../docs/screenshots/regions-${width}.png` });
    await checkbox.press("Escape");
    await expect(trigger).toBeFocused();
    await expect(filter).not.toHaveAttribute("open");
    await trigger.click();
    await page.getByRole("searchbox").click();
    await expect(filter).not.toHaveAttribute("open");
    await trigger.click();
    await filter.getByRole("button", { name: "Done", exact: true }).focus();
    await page.keyboard.press("Tab");
    await expect(filter).not.toHaveAttribute("open");
    if (width < 760) {
      await page.locator(".more-filters summary").click();
      await page.getByRole("button", { name: "Reset view", exact: true }).click();
      await expect(page.locator(".timeline-counter")).toContainText("11 painters");
      await expect(page.locator(".more-filters")).not.toHaveAttribute("open");
      await expect(page.locator(".more-filters summary")).toBeFocused();
    }
  }
});

test("an unrepresented region remains visible and removable even when facets fail", async ({ page }) => {
  await page.route("**/api/backend/v1/timeline/facets", route => route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ error: { message: "Test interrupted" } }) }));
  await page.goto("/?region=unrepresented-region&start=1700&end=1900");
  await expect(page.getByRole("heading", { name: "No painters in this view" })).toBeVisible();
  await page.locator(".multi-filter summary").click();
  const unknown = page.getByRole("checkbox", { name: "unrepresented region", exact: true });
  await expect(unknown).toBeChecked();
  await unknown.click();
  await expect(page.locator(".multi-filter summary")).toBeFocused();
  await expect(page.locator(".timeline-counter")).toContainText("6 painters");
  await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1700");
});
