import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { EventsResponse } from "../lib/events";

async function settled(page: import("@playwright/test").Page, count?: number) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(count === undefined ? /events in this view/ : `${count.toLocaleString("en-GB")} events in this view`);
}

// Real, read-only API and headless Chrome. No database fixtures.
for (const width of [1440, 390, 320]) {
  test(`Events preserves the atlas layout and accessible drawer at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/events"); await settled(page, 100);
    if (width <= 760) await page.getByRole("button", { name: "Filters", exact: true }).click();
    await expect(page.getByRole("checkbox", { name: "Top 100 events", exact: true })).toBeChecked();
    if (width <= 760) await page.getByRole("button", { name: "Close filters", exact: true }).click();
    await expect(page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Events", exact: true })).toHaveAttribute("aria-current", "page");
    await expect(page.getByLabel("Event end year")).toHaveValue("2000");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`events-${width}.png`) });
    await page.getByRole("button", { name: "Open French Revolution", exact: true }).click();
    const panel = page.getByRole("dialog", { name: "Event details" });
    await expect(panel.getByRole("heading", { name: "French Revolution", exact: true })).toBeVisible();
    await expect(panel).toContainText("1789–1799");
    await expect(panel.getByRole("heading", { name: "Why it matters" })).toBeVisible();
    await expect(panel.getByRole("link", { name: /Palace of Versailles/ }).first()).toHaveAttribute("href", /chateauversailles/);
    await expect(panel.getByRole("link", { name: "Books from this period" })).toHaveAttribute("href", /start=1789&end=1799/);
    expect((await new AxeBuilder({ page }).include("dialog").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`event-drawer-${width}.png`) });
    await page.keyboard.press("Escape"); await expect(panel).not.toBeVisible();
    await expect(page.getByRole("button", { name: "Open French Revolution", exact: true })).toBeFocused();
  });
}

test("year pair editing, BCE and the 2000 cutoff work without clamping", async ({ page }) => {
  await page.goto("/events?start=1700&end=1800"); await settled(page);
  const from = page.getByLabel("Event start year"), to = page.getByLabel("Event end year");
  await from.fill("1914"); await from.press("Tab"); await expect(to).toBeFocused();
  await to.fill("1945"); await to.press("Enter");
  await expect(page).toHaveURL(/start=1914&end=1945/); await settled(page);
  await expect(to).toBeFocused();
  await expect(page.getByRole("button", { name: "Open First World War", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open Second World War", exact: true })).toBeVisible();
  await to.fill("2001"); await to.press("Enter");
  await expect(page.locator(".year-inputs").getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(/end=1945/); await to.press("Escape");
  await from.fill("0"); await from.press("Enter"); await expect(page.locator(".year-inputs").getByRole("alert")).toContainText("no year zero");
  await from.fill("-500"); await from.press("Tab"); await to.fill("100"); await to.press("Enter");
  await expect(page).toHaveURL(/start=-500&end=100/); await settled(page);
  await expect(page.locator(".time-title")).toContainText("BCE");
  await page.reload(); await settled(page); await expect(from).toHaveValue("-500"); await expect(to).toHaveValue("100");
});

test("full collection, period drilling, suggestions and history preserve actual counts", async ({ page }) => {
  await page.goto("/events"); await settled(page, 100);
  await page.getByRole("checkbox", { name: "Top 100 events", exact: true }).uncheck(); await settled(page, 10000);
  await expect(page.locator(".period-chart")).toBeVisible();
  const response = await page.request.get("/api/backend/v1/events?top100=false");
  const data: EventsResponse = await response.json();
  expect(data.items).toHaveLength(100); expect(data.hasMore).toBe(true);
  const period = data.density.find(p => p.start_year === 1900)!;
  await page.getByRole("button", { name: new RegExp(`^Explore ${period.start_year}–${period.end_year},`) }).click(); await settled(page, period.count);
  const before = page.url();
  const button = page.locator(".density-actions").getByRole("button", { name: /^Filter by/ }).first();
  const label = (await button.getAttribute("aria-label"))!;
  const count = Number(label.match(/, (\d+) events$/)![1]);
  await button.click(); await settled(page, count);
  expect(new URL(page.url()).searchParams.get("start")).toBe(String(period.start_year));
  await page.reload(); await settled(page, count);
  await page.goBack(); await expect(page).toHaveURL(before); await settled(page, period.count);
  await page.goForward(); await settled(page, count);
});

test("combined country and type filters, pagination and reset", async ({ page }) => {
  await page.goto("/events?top100=false"); await settled(page, 10000);
  await page.locator('summary[aria-label^="Countries:"]').click();
  await page.getByRole("checkbox", { name: "France", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click(); await settled(page);
  await page.locator('summary[aria-label^="Types:"]').click();
  await page.getByRole("checkbox", { name: "Event", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click(); await settled(page);
  const query = new URL(page.url()).searchParams;
  const response = await page.request.get(`/api/backend/v1/events?${query}`); const data: EventsResponse = await response.json();
  await settled(page, data.total); expect(data.total).toBeGreaterThan(0);
  expect(data.items.every(event => event.countries.includes("France") && event.kind === "Event")).toBe(true);
  if (data.hasMore) {
    const first = data.items.map(event => event.id);
    await page.getByRole("button", { name: "Next events", exact: true }).click(); await settled(page, data.total);
    const nextResponse = await page.request.get(`/api/backend/v1/events?${new URL(page.url()).searchParams}`); const next: EventsResponse = await nextResponse.json();
    expect(next.items.some(event => first.includes(event.id))).toBe(false);
  }
  await page.getByRole("button", { name: "Reset view", exact: true }).click(); await settled(page, 100);
  await expect(page.getByRole("checkbox", { name: "Top 100 events", exact: true })).toBeChecked();
  await expect(page.getByLabel("Event start year")).toHaveValue("-12000");
});

test("invalid deep link reports an error and reset recovers", async ({ page }) => {
  await page.goto("/events?start=0&end=2001");
  await expect(page.locator(".timeline-stage").getByRole("alert")).toContainText("We couldn’t load this view");
  await page.getByRole("button", { name: "Reset view", exact: true }).first().click(); await settled(page, 100);
  await page.goto("/events?event=event-does-not-exist");
  await expect(page.getByRole("dialog").getByRole("alert")).toContainText("This event could not be loaded");
  await page.getByRole("button", { name: "Close event details", exact: true }).click();
  await settled(page, 100);
});
