import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

function filter(page: import("@playwright/test").Page, label: string) {
  return page.locator(".multi-filter").filter({ has: page.locator(`summary[aria-label^="${label}:"]`) });
}

test("Monet and Pissarro stay selected across search, drawer, reload and history", async ({ page }) => {
  await page.goto("/");
  const painters = filter(page, "Painters");
  await painters.locator("summary").click();
  await painters.getByRole("searchbox", { name: "Search painters" }).fill("Monet");
  await painters.getByRole("checkbox", { name: "Claude Monet", exact: true }).check();
  await painters.getByRole("searchbox", { name: "Search painters" }).fill("Pissarro");
  await painters.getByRole("checkbox", { name: "Camille Pissarro", exact: true }).check();
  await expect(painters.getByRole("checkbox", { name: "Claude Monet", exact: true })).toBeChecked();
  await painters.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("2 painters in this view");
  expect(new URL(page.url()).searchParams.getAll("painter")).toEqual(["camille-pissarro-q134741", "claude-monet"]);
  await page.reload();
  await expect(page.locator(".timeline-counter")).toContainText("2 painters in this view");
  await page.locator(".artist-mark").filter({ hasText: "Claude Monet" }).click();
  await expect(page.getByRole("dialog", { name: "Painter details", exact: true })).toBeVisible();
  expect(new URL(page.url()).searchParams.get("artist")).toBe("claude-monet");
  expect(new URL(page.url()).searchParams.getAll("painter")).toHaveLength(2);
  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Remove Camille Pissarro filter", exact: true }).click();
  await expect(page.locator(".timeline-counter")).toContainText("1 painter in this view");
  await page.goBack();
  await expect(page.locator(".timeline-counter")).toContainText("2 painters in this view");
  await page.screenshot({ path: "../../docs/screenshots/multiselect-timeline.png" });
});

test("multiple movement and country choices combine on the server", async ({ page }) => {
  await page.goto("/?painter=claude-monet&painter=camille-pissarro-q134741");
  const movements = filter(page, "Movements");
  await movements.locator("summary").click();
  await movements.getByRole("checkbox", { name: "Impressionism", exact: true }).check();
  await movements.getByRole("checkbox", { name: "Post-impressionism", exact: true }).check();
  await movements.getByRole("button", { name: "Done", exact: true }).click();
  const countries = filter(page, "Countries");
  await countries.locator("summary").click();
  await countries.getByRole("checkbox", { name: "France", exact: true }).check();
  await countries.getByRole("checkbox", { name: "Spain", exact: true }).check();
  await countries.getByRole("button", { name: "Done", exact: true }).click();
  const params = new URL(page.url()).searchParams;
  expect(params.getAll("movement")).toHaveLength(2);
  expect(params.getAll("country")).toHaveLength(2);
  const response = await page.request.get(`/api/backend/v1/timeline?${params}`);
  expect(response.ok()).toBe(true);
  const data = await response.json();
  expect(data.items.every((item: { slug: string }) => ["claude-monet", "camille-pissarro-q134741"].includes(item.slug))).toBe(true);
  await expect(page.locator(".timeline-counter")).toContainText(`${data.total} painter`);
});

test("museum discovery carries multiple painters into a scoped collection", async ({ page }) => {
  await page.goto("/museums?artist=claude-monet&artist=camille-pissarro-q134741");
  await expect(page.locator('summary[aria-label="Painters: 2 selected"]')).toBeVisible();
  const first = page.locator('a[href^="/museums/"]').first();
  await expect(first).toBeVisible();
  await first.click();
  const params = new URL(page.url()).searchParams;
  expect(params.getAll("artist")).toHaveLength(2);
  await expect(page.locator('summary[aria-label="Painters: 2 selected"]')).toBeVisible();
  const results = page.getByRole("region", { name: "Museum artwork results" });
  await expect(results).toHaveAttribute("aria-busy", "false");
  const response = await page.request.get(`/api/backend/v1${new URL(page.url()).pathname}/works?${params}`);
  const data = await response.json();
  expect(data.total).toBeGreaterThan(0);
  expect(data.items.every((item: { artists: { slug: string }[] }) => item.artists.some(artist => params.getAll("artist").includes(artist.slug)))).toBe(true);
});

test("open multi-select panels fit phone viewports and support keyboard dismissal", async ({ page }) => {
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 850 });
    await page.goto("/?painter=claude-monet");
    const painters = filter(page, "Painters");
    await painters.locator("summary").click();
    await painters.getByRole("searchbox", { name: "Search painters" }).fill("Pissarro");
    await expect(painters.getByRole("checkbox", { name: "Camille Pissarro", exact: true })).toBeVisible();
    const bounds = (await painters.locator(".multi-filter-panel").boundingBox())!;
    expect(bounds.x).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
    expect(bounds.y + bounds.height).toBeLessThanOrEqual(850);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: `../../docs/screenshots/multiselect-open-${width}.png` });
    await page.keyboard.press("Escape");
    await expect(painters.locator("summary")).toBeFocused();
    await expect(painters).not.toHaveAttribute("open");
  }
});

test("museum work types and venue multi-selects stay usable on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 850 });
  await page.goto("/museums/the-met");
  await page.getByText("More artwork filters", { exact: true }).click();
  const types = filter(page, "Work types");
  await types.locator("summary").click();
  await types.getByRole("checkbox", { name: "painting", exact: true }).check();
  await types.getByRole("checkbox", { name: "fresco", exact: true }).check();
  await types.getByRole("button", { name: "Done", exact: true }).click();
  expect(new URL(page.url()).searchParams.getAll("work_type")).toHaveLength(2);
  const venues = filter(page, "Confirmed at venues");
  await venues.locator("summary").click();
  const options = venues.getByRole("checkbox");
  await expect(options).toHaveCount(2);
  await options.nth(0).check();
  await options.nth(1).check();
  const bounds = (await venues.locator(".multi-filter-panel").boundingBox())!;
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390);
  await page.screenshot({ path: "../../docs/screenshots/multiselect-museum-390.png" });
  await venues.getByRole("button", { name: "Done", exact: true }).click();
  expect(new URL(page.url()).searchParams.getAll("venue")).toHaveLength(2);
  await expect(page.getByRole("heading", { name: "No matching works are confirmed on view" })).toBeVisible();
});
