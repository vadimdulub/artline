import { expect, test } from "@playwright/test";

test("Books gives modern dates more space in the chart and slider without changing the selection", async ({ page }, testInfo) => {
  await page.goto("/books");
  await expect(page.locator(".timeline-counter")).toContainText("100 books in this view");
  await expect(page.locator(".book-scale-break")).toHaveCSS("left", `${(await page.locator(".timeline-stage").boundingBox())!.width / 4}px`);
  await expect(page.getByText("Before 1700 is compressed", { exact: false })).toHaveCount(0);
  await expect(page.getByText("Focus the timeline", { exact: true })).toHaveCount(0);
  await expect(page.locator(".preset-group")).toHaveCount(0);
  await expect(page.getByText("Move the range · 10 years", { exact: true })).toHaveCount(0);
  await expect(page.locator('[class*="coverTitle"], [class*="coverImage"]')).toHaveCount(0);
  await expect(page.locator(".range-scale-marker")).toHaveText(["1700", "1750", "1800", "1850", "1900", "1950"]);
  const frankenstein = page.locator(".book-mark").filter({ hasText: "Frankenstein" });
  const position = await frankenstein.evaluate(el => parseFloat((el as HTMLElement).style.left));
  expect(position).toBeGreaterThan(50);
  expect(position).toBeLessThan(55);
  await page.screenshot({ path: testInfo.outputPath("books-compressed-full.png") });

  const start = page.getByLabel("Book start year"), end = page.getByLabel("Book end year");
  const handle = page.getByLabel("Timeline start handle");
  await start.fill("1731");
  await start.press("Enter");
  await expect(handle).toHaveAttribute("aria-valuenow", "1731");
  const handlePosition = Number(await handle.inputValue()) / 100000;
  expect(handlePosition).toBeGreaterThan(.30);
  expect(handlePosition).toBeLessThan(.33);
  await expect(page.locator(".book-scale-break")).toHaveCount(1);
  await expect(page.locator(".timeline-counter")).toContainText("58 books in this view");
  await page.screenshot({ path: testInfo.outputPath("books-modern-range-slider.png") });
  await handle.focus();
  await page.keyboard.press("ArrowRight");
  await expect(start).toHaveValue("1732");
  await page.keyboard.press("ArrowLeft");
  await expect(start).toHaveValue("1731");

  // Drag the native handle into the middle of the expanded modern segment.
  const track = (await page.locator(".range-track").boundingBox())!;
  await page.mouse.move(track.x + track.width * handlePosition, track.y + track.height / 2);
  await page.mouse.down();
  await page.mouse.move(track.x + track.width * .5, track.y + track.height / 2, { steps: 8 });
  await page.mouse.up();
  await expect.poll(async () => Number(await start.inputValue())).toBeGreaterThanOrEqual(1798);
  expect(Number(await start.inputValue())).toBeLessThanOrEqual(1802);
  await expect(end).toHaveValue("2000");

  // Moving a selected window preserves its width within the modern segment.
  await start.fill("1750"); await start.press("Enter");
  await end.fill("1850"); await end.press("Enter");
  const window = (await page.getByRole("button", { name: "Move selected time range", exact: true }).boundingBox())!;
  await page.mouse.move(window.x + window.width / 2, window.y + window.height / 2);
  await page.mouse.down();
  await page.mouse.move(window.x + window.width / 2 + track.width * .05, window.y + window.height / 2, { steps: 8 });
  await page.mouse.up();
  expect(Number(await end.inputValue()) - Number(await start.inputValue())).toBe(100);
  expect(Number(await start.inputValue())).toBeGreaterThan(1760);
});

test("earlier selections retain the complete axis and compressed controls remain usable on phones", async ({ page }, testInfo) => {
  await page.goto("/books?start=1200&end=1700");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".book-scale-break")).toHaveCount(1);
  const quixote = page.locator(".book-mark").filter({ hasText: "Don Quixote" });
  expect(await quixote.evaluate(el => parseFloat((el as HTMLElement).style.left))).toBeCloseTo(23.88, 0);
  await page.goto("/books?start=-1&end=20");
  await page.getByLabel("Timeline start handle").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByLabel("Book start year")).toHaveValue("1");
  await page.keyboard.press("ArrowLeft");
  await expect(page.getByLabel("Book start year")).toHaveValue("-1");

  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books");
    await expect(page.locator(".timeline-counter")).toContainText("100 books in this view");
    await expect(page.locator(".tick-row").getByText("1700", { exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: testInfo.outputPath(`books-compressed-${width}.png`) });
    await page.locator(".range-track").scrollIntoViewIfNeeded();
    await expect(page.locator(".range-scale-marker")).toHaveText(width >= 390 ? ["1700", "1800", "1900"] : ["1700", "1800"]);
    const firstLabel = (await page.locator(".range-endpoints > span").first().boundingBox())!;
    const scaleLabel = (await page.locator(".range-scale-marker").first().boundingBox())!;
    expect(scaleLabel.x).toBeGreaterThan(firstLabel.x + firstLabel.width + 4);
    const labels = await page.locator(".range-scale-marker, .range-endpoints > span").evaluateAll(nodes => nodes.map(node => {
      const rect = node.getBoundingClientRect(); return { left: rect.left, right: rect.right };
    }).sort((a, b) => a.left - b.left));
    for (let i = 1; i < labels.length; i++) expect(labels[i].left).toBeGreaterThan(labels[i - 1].right + 4);
    await page.screenshot({ path: testInfo.outputPath(`books-slider-${width}.png`) });
  }
});
