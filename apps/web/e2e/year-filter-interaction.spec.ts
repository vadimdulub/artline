import { expect, test, type Page } from "@playwright/test";

async function grip(page: Page, side: "start" | "end") {
  return page.getByLabel(`Timeline ${side} handle`).evaluate((input: HTMLInputElement) => {
    const track = input.parentElement!.getBoundingClientRect();
    const box = input.getBoundingClientRect();
    const fraction = (Number(input.value) - Number(input.min)) / (Number(input.max) - Number(input.min));
    return { x: track.x + track.width * fraction + parseFloat(getComputedStyle(input).getPropertyValue("--handle-offset") || "0"), y: box.y + box.height / 2 };
  });
}

// Real Chrome interactions and real read-only catalogue responses. No mocks.
for (const route of ["/books", "/", "/events", "/all"]) {
  test(`${route} accepts a new year pair without clamping to the previous range`, async ({ page }) => {
    await page.goto(`${route}?${route === "/all" ? "selection=true&type=book&" : ""}start=1800&end=1900`);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    const fields = page.locator(".year-inputs input"), from = fields.first(), to = fields.last();
    await from.fill("1950"); await from.press("Tab");
    await expect(to).toBeFocused();
    await expect(from).toHaveValue("1950");
    await to.fill("2000"); await to.press("Enter");
    await expect(from).toHaveValue("1950");
    await expect(to).toHaveValue("2000");
    await expect(to).toBeFocused();
    await expect(page).toHaveURL(/start=1950&end=2000/);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await expect(page.locator(".time-title")).toContainText("1950");
    await page.reload();
    await expect(from).toHaveValue("1950");
    await expect(to).toHaveValue("2000");
  });

  test(`${route} close handles stay distinct and expand independently`, async ({ page }) => {
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 950 });
      for (const side of ["start", "end"] as const) {
        await page.goto(`${route}?${route === "/all" ? "selection=true&type=book&" : ""}start=1800&end=1801`);
        await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
        await page.locator(".range-track").scrollIntoViewIfNeeded();
        const track = (await page.locator(".range-track").boundingBox())!;
        const handle = await grip(page, side), other = await grip(page, side === "start" ? "end" : "start");
        expect(Math.abs(handle.x - other.x)).toBeGreaterThanOrEqual(31.9);
        expect(handle.y).toBe(other.y);
        expect(handle.x).toBeGreaterThanOrEqual(track.x - 1);
        expect(handle.x).toBeLessThanOrEqual(track.x + track.width + 1);
        const before = page.url();
        await page.mouse.move(handle.x, handle.y);
        await page.mouse.down();
        await page.mouse.move(handle.x + track.width * (side === "start" ? -.1 : .1), handle.y, { steps: 15 });
        // Only preview during the drag; avoid moving the mobile chart underneath it.
        expect(page.url()).toBe(before);
        await page.mouse.up();
        const fields = page.locator(".year-inputs input");
        if (side === "start") {
          await expect.poll(async () => Number(await fields.first().inputValue())).toBeLessThan(1790);
          await expect(fields.last()).toHaveValue("1801");
        } else {
          await expect.poll(async () => Number(await fields.last().inputValue())).toBeGreaterThan(1810);
          await expect(fields.first()).toHaveValue("1800");
        }
        await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
      }
    }
  });

  test(`${route} invalid dates stay editable and never change the catalogue`, async ({ page }) => {
    await page.goto(`${route}?${route === "/all" ? "selection=true&type=book&" : ""}start=1800&end=1900`);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    const fields = page.locator(".year-inputs input"), from = fields.first(), to = fields.last();
    const original = page.url();
    await from.fill("1950"); await from.press("Enter");
    await expect(page.locator(".year-inputs").getByRole("alert")).toContainText("From must be earlier");
    await expect(from).toHaveValue("1950");
    await expect(from).toBeFocused();
    expect(page.url()).toBe(original);
    await from.press("Escape");
    await expect(from).toHaveValue("1800");
    await expect(page.locator(".year-inputs").getByRole("alert")).not.toBeVisible();
    await to.fill(""); await to.press("Enter");
    await expect(page.locator(".year-inputs").getByRole("alert")).toContainText("whole year");
    expect(page.url()).toBe(original);
    await to.press("Escape");
    await from.fill("1850"); await from.press("Tab"); await to.press("Tab");
    await expect(page).toHaveURL(/start=1850&end=1900/);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    const api = route === "/all" ? "/api/backend/v1/atlas?selection=true&type=book&start=1850&end=1900&highlights=true" : route === "/" ? "/api/backend/v1/timeline?popular=true&start=1850&end=1900" : `/api/backend/v1${route}?top100=true&start=1850&end=1900`;
    const response = await page.request.get(api);
    expect(response.ok()).toBe(true);
    const data = await response.json();
    if (route === "/all") await expect(page.locator(".all-canvas-heading [role=status]")).toHaveText(`${data.total.toLocaleString("en-GB")} entries`);
    else await expect(page.locator(".timeline-counter")).toContainText(`${data.total} ${route === "/" ? "painters" : route.slice(1)} in this view`);
  });
}

test("Books rejects year zero and accepts a BCE-to-modern draft", async ({ page }) => {
  await page.goto("/books?start=1800&end=1900");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const from = page.getByLabel("Book start year"), to = page.getByLabel("Book end year");
  await from.fill("0"); await from.press("Enter");
  await expect(page.locator(".year-inputs").getByRole("alert")).toContainText("no year zero");
  await expect(page).toHaveURL(/start=1800&end=1900/);
  await from.fill("-800"); await from.press("Tab"); await to.fill("100"); await to.press("Enter");
  await expect(page).toHaveURL(/start=-800&end=100/);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".time-title")).toContainText("BCE");
});

test("touch dragging previews the year range and cancellation restores it", async ({ browser, baseURL }) => {
  const context = await browser.newContext({ baseURL, viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const touch = await context.newCDPSession(page);
  for (const route of ["/books", "/", "/events", "/all"]) {
    await page.goto(`${route}?${route === "/all" ? "selection=true&type=book&" : ""}start=1800&end=1801`);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    await page.locator(".range-track").scrollIntoViewIfNeeded();
    for (const commit of [false, true]) {
      const box = (await page.locator(".range-track").boundingBox())!;
      const original = page.url();
      const { x, y } = await grip(page, "start");
      await touch.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
      await touch.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x: x - box.width * .1, y }] });
      await expect.poll(async () => Number(await page.locator(".year-inputs input").first().inputValue())).toBeLessThan(1790);
      expect(page.url()).toBe(original);
      await touch.send("Input.dispatchTouchEvent", { type: commit ? "touchEnd" : "touchCancel", touchPoints: [] });
      if (commit) {
        await expect.poll(() => page.url()).not.toBe(original);
        await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
      } else {
        await expect(page.locator(".year-inputs input").first()).toHaveValue("1800");
        expect(page.url()).toBe(original);
      }
    }
  }
  await context.close();
});
