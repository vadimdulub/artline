import { expect, test, type Locator, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mobileAtlasMetadata, mockMobileExplorers } from "./mobile-explorer-fixture";

const views = [
  ["paintings", "/?view=paintings&start=1300&end=1650"],
  ["painters", "/?start=1300&end=1650"],
  ["books", "/books"],
  ["events", "/events"],
  ["all", "/all?preset=renaissance"],
] as const;
test.beforeEach(async ({ page }) => { await mockMobileExplorers(page); });

async function swipeUp(page: Page, container: Locator) {
  const box = (await container.boundingBox())!;
  const touch = await page.context().newCDPSession(page);
  await touch.send("Emulation.setTouchEmulationEnabled", { enabled: true });
  const x = box.x + box.width / 2, from = box.y + box.height * .8, to = box.y + box.height * .2;
  await touch.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y: from }] });
  for (let step = 1; step <= 8; step++) {
    await touch.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x, y: from + (to - from) * step / 8 }] });
    await page.evaluate(() => new Promise(requestAnimationFrame));
  }
  await touch.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
  await touch.detach();
}

for (const width of [320, 390, 430]) for (const [name, route] of views) {
  test(`${name}: visible mobile slider and content at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 844 });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(route);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.locator(".range-track")).toBeInViewport();
    await expect.poll(async () => { const box = (await page.locator(".range-track").boundingBox())!; return box.y + box.height; }).toBeLessThanOrEqual(844);
    await expect(page.getByRole("slider", { name: "Timeline start handle" })).toBeVisible();
    await expect(page.getByRole("slider", { name: "Timeline end handle" })).toBeVisible();
    await expect(page.getByRole("spinbutton")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /edit dates|done editing dates|move range .*earlier|move range .*later/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Done editing dates" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Zoom out to all years" })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    expect((await page.locator(".timeline-stage").boundingBox())!.height).toBeGreaterThan(160);
    if (name === "paintings" || name === "all") {
      await expect(page.locator(".all-artwork-card").first()).toBeInViewport();
      expect((await page.locator(".all-artwork-image").first().boundingBox())!.height).toBeGreaterThanOrEqual(190);
      if (name === "paintings") expect((await page.locator(".all-artwork-image").first().boundingBox())!.width).toBeCloseTo(width - 32, 0);
      if (process.env.ARTLINE_MOBILE_IMAGE_DIR) await expect.poll(() => page.locator(".all-artwork-card img").first().evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
    }
    if (name === "books") await expect(page.getByRole("button", { name: "Scroll books right" })).toBeInViewport();
    await page.screenshot({ path: info.outputPath(`${name}-${width}.png`) });
    if (width === 320) expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    expect(errors).toEqual([]);
  });
}

for (const [name, route] of views) test(`${name}: mobile range changes persist through full view and rotation`, async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(route);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const handle = page.getByRole("slider", { name: "Timeline start handle" });
  const original = Number(await handle.getAttribute("aria-valuenow"));
  await handle.press("ArrowRight");
  await expect.poll(() => new URL(page.url()).searchParams.get("start")).toBe(String(original === -1 ? 1 : original + 1));
  const url = page.url();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  await expect(page.locator(".range-track")).toBeInViewport();
  await page.setViewportSize({ width: 1024, height: 1000 });
  await expect(handle).toBeVisible();
  await handle.focus();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole("spinbutton")).toHaveCount(0);
  await expect(handle).toBeFocused();
  await expect(page.locator(".range-track")).toBeInViewport();
  await page.keyboard.press("Escape");
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "false");
  await expect(page).toHaveURL(url);
  await page.reload();
  await expect(handle).toHaveAttribute("aria-valuenow", String(original === -1 ? 1 : original + 1));
});

for (const width of [768, 1024, 1440]) test(`desktop dates use the handles at ${width}px`, async ({ page }) => {
  await page.setViewportSize({ width, height: 1000 });
  for (const [, route] of views) {
    await page.goto(route);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.getByRole("slider", { name: "Timeline start handle" })).toBeVisible();
    await expect(page.getByRole("slider", { name: "Timeline end handle" })).toBeVisible();
    await expect(page.getByRole("spinbutton")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /zoom out to all years|edit dates|done editing dates|move range .*earlier|move range .*later/i })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

test("All starting points scroll by touch in full view and the last period can be selected", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/api/backend/v1/atlas/presets", route => route.fulfill({ json: {
    ...mobileAtlasMetadata,
    presets: [...mobileAtlasMetadata.presets, ...Array.from({ length: 12 }, (_, index) => ({
      ...mobileAtlasMetadata.presets[0], id: `period-${index + 1}`, name: `Period ${index + 1}`,
    }))],
  } }));
  await page.goto("/all");
  await expect(page.getByRole("heading", { name: "Explore a moment in history" })).toBeVisible();
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  const canvas = page.locator(".all-empty-canvas");
  await expect(page.locator("body")).toHaveCSS("overflow", "hidden");
  await swipeUp(page, canvas);
  await expect.poll(() => canvas.evaluate(element => element.scrollTop)).toBeGreaterThan(50);
  await page.getByRole("button", { name: "Period 12", exact: true }).click();
  await expect(page).toHaveURL(/preset=period-12/);
  await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "true");
  await expect(page.locator(".all-artwork-card").first()).toBeVisible();
  await page.screenshot({ path: info.outputPath("all-full-view-selected.png") });
});

test("All populated lanes scroll by touch in short full view", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto("/all?preset=renaissance");
  await expect(page.locator(".all-lane")).toHaveCount(3);
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  const stage = page.locator(".timeline-stage");
  await swipeUp(page, stage);
  await expect.poll(() => stage.evaluate(element => element.scrollTop)).toBeGreaterThan(20);
  await expect(page.locator(".range-track")).toBeInViewport();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeInViewport();
});

test("Books full view keeps the date handles visible on short screens", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/books");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  for (const size of [{ width: 390, height: 844 }, { width: 320, height: 568 }, { width: 740, height: 390 }]) {
    await page.setViewportSize(size);
    await expect(page.locator(".range-track")).toBeInViewport();
    await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeInViewport();
  }
});

test("the movement colour key is in the mobile header and can filter painters", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?start=1300&end=1650");
  const key = page.locator(".timeline-compact-heading .movement-key");
  await expect(key).toBeInViewport();
  await key.locator("summary").click();
  await key.getByRole("button", { name: "Renaissance", exact: true }).click();
  await expect(page).toHaveURL(/movement=renaissance/);
  await expect(page.getByRole("button", { name: "Zoom out to all years" })).toHaveCount(0);
});

test("full view enlarges paintings and the date slider stays visible in landscape", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?view=paintings&start=1300&end=1650");
  const image = page.locator(".all-artwork-image").first();
  await expect(image).toBeVisible();
  const before = (await image.boundingBox())!.height;
  await page.getByRole("button", { name: "Full view", exact: true }).click();
  expect((await image.boundingBox())!.height).toBeGreaterThan(before);
  await expect(page.locator(".range-track")).toBeInViewport();
  await page.setViewportSize({ width: 740, height: 390 });
  await expect(page.locator(".range-track")).toBeInViewport();
  await expect(page.getByRole("button", { name: "Exit full view", exact: true })).toBeInViewport();
  await page.screenshot({ path: info.outputPath("landscape-full-view.png") });
});

test("dragging dates previews the range before saving it on release", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/events?start=1800&end=1900");
  const track = page.locator(".range-track");
  await expect(track).toBeInViewport();
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
