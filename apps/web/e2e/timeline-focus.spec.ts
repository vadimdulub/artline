import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const zoomOut = (page: Page) => page.getByRole("button", { name: "Zoom out to all years", exact: true });
const ticks = (page: Page) => page.locator(".tick-row > span").evaluateAll(nodes => nodes.map(node => ({ label: node.textContent, left: (node as HTMLElement).style.left })));
async function ready(page: Page) {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toHaveCount(0);
}
async function fitted(page: Page, start: number, end: number) {
  const label = (year: number) => year < 0 ? `${Math.abs(year)} BCE` : String(year);
  const axis = await ticks(page);
  expect(axis[0]).toEqual({ label: label(start), left: "0%" });
  expect(axis.at(-1)).toEqual({ label: label(end), left: "100%" });
  await expect(zoomOut(page)).toBeEnabled();
  await expect(page.locator(".book-scale-break,.timeline-selected-years")).toHaveCount(0);
}

for (const width of [1440, 320]) {
  for (const view of [
    { name: "Books", path: "/books?top100=true", start: 1600, end: 1800, minimum: -5000 },
    { name: "Authors", path: "/books?top100=true&view=authors", start: 1600, end: 1800, minimum: -5000 },
    { name: "Arts", path: "/?popular=true&country=IT", start: 1300, end: 1650, minimum: 1100 },
    { name: "Events", path: "/events?top100=true", start: 1700, end: 1800, minimum: -12000 },
  ]) test(`${view.name} shares focus and zoom out at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto(`${view.path}&start=${view.start}&end=${view.end}`);
    await ready(page); await fitted(page, view.start, view.end);
    const marks = page.locator(".timeline-mark");
    expect(await marks.count()).toBeGreaterThan(0);
    expect(await marks.evaluateAll(nodes => nodes.every(node => {
      const mark = node.getBoundingClientRect(), canvas = node.closest(".artist-field")!.getBoundingClientRect();
      return mark.left >= canvas.left - 0.5 && mark.right <= canvas.right + 0.5;
    }))).toBe(true);
    const geometry = await page.locator(".tick-row > span").evaluateAll(nodes => nodes.map(node => {
      const range = document.createRange(); range.selectNodeContents(node);
      const rect = range.getBoundingClientRect(); return { left: rect.left, right: rect.right };
    }));
    expect(geometry.every((rect, index) => rect.left >= 0 && rect.right <= width && (!index || rect.left > geometry[index - 1].right))).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`${view.name.toLowerCase()}-focus-${width}.png`) });
    await zoomOut(page).focus(); await zoomOut(page).press("Enter"); await ready(page);
    await expect(zoomOut(page)).toBeDisabled();
    await expect(page.locator(".year-inputs input").first()).toHaveValue(String(view.minimum));
    await expect(page.locator(".year-inputs input").last()).toHaveValue("2000");
    expect(new URL(page.url()).searchParams.has("start")).toBe(false);
    expect(new URL(page.url()).searchParams.has("end")).toBe(false);
    for (const [key, value] of new URL(view.path, "http://localhost").searchParams) {
      expect(new URL(page.url()).searchParams.get(key)).toBe(value);
    }
    await page.goBack(); await ready(page); await fitted(page, view.start, view.end);
    await page.reload(); await ready(page); await fitted(page, view.start, view.end);
    const fields = page.locator(".year-inputs input");
    await fields.first().fill("1939"); await fields.last().fill("1945"); await fields.last().press("Enter");
    await ready(page); await fitted(page, 1939, 1945);
  });
}

for (const view of [{ path: "/?popular=false", endpoint: "timeline" }, { path: "/books?top100=false", endpoint: "books" }, { path: "/events?top100=false", endpoint: "events" }]) {
  test(`${view.endpoint} refits density periods and ignores a late range response`, async ({ page }) => {
    await page.goto(view.path); await ready(page);
    await page.locator(".period-column").filter({ hasText: /1800/ }).first().click();
    await ready(page);
    const fields = page.locator(".year-inputs input");
    await fitted(page, Number(await fields.first().inputValue()), Number(await fields.last().inputValue()));
    let release!: () => void;
    const gate = new Promise<void>(resolve => { release = resolve; });
    let held = false;
    await page.route(`**/api/backend/v1/${view.endpoint}?*`, async route => {
      if (new URL(route.request().url()).searchParams.get("start") !== "1939") return route.continue();
      const response = await route.fetch(); held = true; await gate;
      await route.fulfill({ response }).catch(() => {});
    });
    try {
      await fields.first().fill("1939"); await fields.last().fill("1945"); await fields.last().press("Enter");
      await expect.poll(() => held).toBe(true);
      await fitted(page, 1939, 1945);
      await expect(page.locator(".period-column,.timeline-mark")).toHaveCount(0);
      await zoomOut(page).click(); await ready(page);
      await expect(zoomOut(page)).toBeDisabled();
    } finally { release(); await page.unrouteAll({ behavior: "wait" }); }
    await expect(zoomOut(page)).toBeDisabled();
    await expect(page.locator(".period-column").first()).toBeVisible();
  });
}

for (const [start, end] of [[-500, -100], [-1, 1], [1399, 1401], [1699, 1701], [1999, 2000]]) {
  test(`Events focuses ${start}–${end} without a year zero or compressed gap`, async ({ page }) => {
    await page.goto(`/events?start=${start}&end=${end}`); await ready(page); await fitted(page, start, end);
    expect((await ticks(page)).some(tick => tick.label === "0")).toBe(false);
    await zoomOut(page).click(); await ready(page);
    await expect(zoomOut(page)).toBeDisabled();
    await expect(page.getByLabel("Event start year", { exact: true })).toHaveValue("-12000");
    await page.goBack(); await ready(page); await fitted(page, start, end);
  });
}

test("Events zoom out preserves every event filter and clears pagination", async ({ page }) => {
  const filters = "q=war&top100=false&country=France&country=United+Kingdom&topic=Conflict&region=Western+Europe&kind=Event";
  await page.goto(`/events?${filters}&start=1900&end=1950`); await ready(page);
  const next = page.getByRole("button", { name: "Next events", exact: true });
  if (await next.count()) { await next.click(); await ready(page); }
  await zoomOut(page).click(); await ready(page);
  const query = new URL(page.url()).searchParams;
  for (const [key, value] of new URLSearchParams(filters)) expect(query.getAll(key)).toContain(value);
  for (const key of ["start", "end", "after"]) expect(query.has(key)).toBe(false);
  await expect(zoomOut(page)).toBeDisabled();
});

test("Events clips overlapping periods to the focused canvas", async ({ page }) => {
  await page.goto("/events?start=1928&end=1929"); await ready(page); await fitted(page, 1928, 1929);
  const revolution = page.locator(".timeline-mark").filter({ hasText: "Chinese Communist Revolution" });
  await expect(revolution).toHaveCSS("left", "0px");
  const mark = (await revolution.boundingBox())!, canvas = (await page.locator(".artist-field").boundingBox())!;
  expect(Math.abs(mark.width - canvas.width)).toBeLessThan(1);
  await expect(revolution).toContainText("1927–1949");
  await revolution.click();
  await expect(page.getByRole("dialog", { name: "Event details" })).toContainText("1927–1949");
});

test("Events zoom out recovers from an invalid interval without clearing filters", async ({ page }) => {
  await page.goto("/events?q=war&top100=false&start=0&end=2001");
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toBeVisible();
  await expect(zoomOut(page)).toBeEnabled();
  await zoomOut(page).click(); await ready(page);
  await expect(zoomOut(page)).toBeDisabled();
  await expect(page.getByRole("searchbox", { name: "Find an event" })).toHaveValue("war");
  expect(new URL(page.url()).searchParams.get("top100")).toBe("false");
});
