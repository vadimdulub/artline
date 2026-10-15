import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mockMobileExplorers } from "./mobile-explorer-fixture";

const views = [
  ["paintings", "/?view=paintings&start=1300&end=1650"],
  ["painters", "/?start=1300&end=1650"],
  ["books", "/books"],
  ["events", "/events"],
  ["all", "/all?preset=renaissance"],
] as const;
test.beforeEach(async ({ page }) => { await mockMobileExplorers(page); });

for (const width of [320, 390, 430]) for (const [name, route] of views) {
  test(`${name}: one mobile date bar and content space at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(route);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.locator(".range-mobile-toggle")).toBeVisible();
    await expect(page.locator(".range-editor")).toBeHidden();
    expect((await page.locator(".timeline-heading-title").boundingBox())!.height).toBeLessThanOrEqual(1);
    expect((await page.locator(".timeline-focus").boundingBox())!.height).toBeLessThanOrEqual(52);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    for (const control of await page.locator(".range-mobile-bar button, .timeline-zoom-out").all()) {
      await expect(control).toBeInViewport();
      expect((await control.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    }
    const stage = (await page.locator(".timeline-stage").boundingBox())!;
    expect(stage.height).toBeGreaterThan(420);
    if (name === "paintings" || name === "all") {
      await expect(page.locator(".all-artwork-card").first()).toBeInViewport();
      expect((await page.locator(".all-artwork-image").first().boundingBox())!.height).toBeGreaterThanOrEqual(190);
      if (process.env.ARTLINE_MOBILE_IMAGE_DIR) await expect.poll(() => page.locator(".all-artwork-card img").first().evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
    }
    if (name === "books") {
      await expect(page.getByRole("button", { name: "Scroll books right" })).toBeInViewport();
      await expect(page.locator(".library-card").first()).toBeInViewport();
    }
    await page.screenshot({ path: info.outputPath(`${name}-${width}.png`) });
    if (width === 320) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(errors).toEqual([]);
  });
}

for (const [name, route] of views) test(`${name}: date editing, collapse, full view and rotation`, async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto(route);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const toggle = page.locator(".range-mobile-toggle");
  await toggle.click();
  const from = page.locator(".year-inputs input").first(), to = page.locator(".year-inputs input").last();
  await expect(from).toBeVisible();
  await from.fill("1500"); await from.press("Tab"); await expect(to).toBeFocused();
  await to.fill("1600"); await to.press("Enter");
  await expect(page).toHaveURL(/start=1500&end=1600/);
  await to.press("Escape");
  await expect(toggle).toBeFocused();
  await expect(toggle).toContainText("1500 – 1600");
  await expect(from).toBeHidden();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await toggle.click(); await from.focus(); await from.press("Escape");
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "true");
  await expect(toggle).toBeFocused();
  await toggle.click(); await from.focus();
  await page.setViewportSize({ width: 1024, height: 768 });
  await expect(from).toBeVisible(); await expect(toggle).toBeHidden();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(from).toBeVisible(); await expect(from).toBeFocused();
  await from.press("Escape"); await page.keyboard.press("Escape");
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "false");
  await page.reload();
  await expect(toggle).toContainText("1500 – 1600");
  await expect(from).toBeHidden();
});

for (const width of [768, 1024, 1440]) test(`desktop dates remain directly editable at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  for (const [, route] of views) {
    await page.goto(route);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.locator(".range-mobile-bar")).toBeHidden();
    await expect(page.locator(".year-inputs input").first()).toBeVisible();
    expect((await page.locator(".timeline-heading-title").boundingBox())!.height).toBeGreaterThan(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

test("BCE dates, invalid years and keyboard range handles stay usable", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await page.goto("/events?start=-500&end=100");
  const toggle = page.locator(".range-mobile-toggle");
  await expect(toggle).toContainText("500 BCE – 100");
  await toggle.click();
  const from = page.getByLabel("Event start year");
  await from.fill("0"); await from.press("Enter");
  await expect(page.locator(".year-error")).toContainText("no year zero");
  await expect(page).toHaveURL(/start=-500&end=100/);
  await from.press("Escape"); await toggle.click();
  await page.getByLabel("Timeline start handle").press("ArrowRight");
  await expect(page).toHaveURL(/start=-499&end=100/);
  await page.getByRole("button", { name: "Done editing dates" }).click();
  await expect(toggle).toContainText("499 BCE – 100");
  await page.getByRole("button", { name: "Move range 1 year earlier" }).click();
  await expect(toggle).not.toContainText("499 BCE – 100");
});

test("dates apply on Done, and short landscape full view stays reachable", async ({ page }, info) => {
  await page.setViewportSize({ width: 740, height: 390 });
  await page.goto("/?view=paintings&start=1300&end=1650");
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await page.locator(".range-mobile-toggle").click();
  await page.getByLabel("Start year", { exact: true }).fill("1400");
  await page.getByRole("button", { name: "Done editing dates" }).click();
  await expect(page).toHaveURL(/start=1400/);
  await expect(page.locator(".range-mobile-toggle")).toContainText("1400 – 1650");
  await expect(page.locator(".all-artwork-card").first()).toBeVisible();
  await page.getByRole("button", { name: "Filters", exact: true }).click();
  await expect(page.getByRole("button", { name: "Close filters", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close filters", exact: true }).click();
  await page.locator(".range-mobile-toggle").scrollIntoViewIfNeeded();
  await expect(page.locator(".range-mobile-toggle")).toBeInViewport();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(740);
  await page.screenshot({ path: info.outputPath("landscape-full-view.png") });
});

test("All keeps its loading spinner and recoverable error in the compact layout", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  let release!: () => void;
  const pending = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/backend/v1/atlas?**", async route => {
    await pending;
    await route.fulfill({ status: 503, json: { error: { message: "Temporary test outage" } } });
  });
  await page.goto("/all?preset=renaissance");
  await expect(page.locator(".all-content-loading .loading-spinner")).toBeVisible();
  await expect(page.locator(".range-mobile-toggle")).toBeInViewport();
  release();
  await expect(page.getByRole("heading", { name: "We couldn’t load this view" })).toBeVisible();
  await expect(page.locator(".all-content-loading")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Retry", exact: true })).toBeInViewport();
});

test("full view gives paintings more image space without changing the range", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?view=paintings&start=1300&end=1650");
  const image = page.locator(".all-artwork-image").first();
  await expect(image).toBeVisible();
  const before = (await image.boundingBox())!.height;
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  expect((await image.boundingBox())!.height).toBeGreaterThan(before);
  await expect(page.locator(".range-mobile-toggle")).toBeInViewport();
  await expect(page.locator(".range-mobile-toggle")).toContainText("1300 – 1650");
});

test("opening mobile dates remeasures the draggable range", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/events?start=1800&end=1900");
  await page.locator(".range-mobile-toggle").click();
  const track = page.locator(".range-track"); await track.scrollIntoViewIfNeeded();
  const grip = await page.getByLabel("Timeline start handle").evaluate((input: HTMLInputElement) => {
    const box = input.parentElement!.getBoundingClientRect();
    const fraction = (Number(input.value) - Number(input.min)) / (Number(input.max) - Number(input.min));
    return { x: box.x + box.width * fraction + parseFloat(getComputedStyle(input).getPropertyValue("--handle-offset") || "0"), y: box.y + box.height / 2 };
  });
  const url = page.url();
  await page.mouse.move(grip.x, grip.y); await page.mouse.down();
  await page.mouse.move(grip.x - 24, grip.y, { steps: 8 });
  expect(page.url()).toBe(url);
  await page.mouse.up();
  await expect.poll(() => Number(new URL(page.url()).searchParams.get("start"))).toBeLessThan(1800);
  expect(new URL(page.url()).searchParams.get("end")).toBe("1900");
});
