import { expect, test } from "@playwright/test";

test("ArtWorks compresses 1100–1400 and keeps numeric slider years usable", async ({ page }, testInfo) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    const stage = (await page.locator(".timeline-stage").boundingBox())!;
    expect(await page.locator(".book-scale-break").evaluate(el => parseFloat((el as HTMLElement).style.left))).toBeCloseTo(15);
    const year1400 = page.locator(".tick-row").getByText("1400", { exact: true });
    await expect(year1400).toBeVisible();
    const marker = page.locator(".range-scale-marker").getByText("1400", { exact: true });
    await expect(marker).toBeVisible();
    expect(stage.width).toBeGreaterThan(250);
    await expect(page.locator(".range-endpoints")).toHaveText("11002000");
    await expect(page.locator(".range-pan")).not.toContainText("Move the range");
    await page.locator(".range-track").scrollIntoViewIfNeeded();
    const labels = await page.locator(".range-scale-marker, .range-endpoints > span").evaluateAll(nodes => nodes.map(node => {
      const rect = node.getBoundingClientRect(); return { left: rect.left, right: rect.right };
    }).sort((a, b) => a.left - b.left));
    for (let i = 1; i < labels.length; i++) expect(labels[i].left).toBeGreaterThan(labels[i - 1].right + 4);
    await page.screenshot({ path: testInfo.outputPath(`artworks-years-${width}.png`) });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
  const start = page.getByLabel("Start year", { exact: true }), end = page.getByLabel("End year", { exact: true });
  await start.fill("1400"); await start.press("Enter");
  await expect(page.getByLabel("Timeline start handle")).toHaveValue("15000");
  await expect(page.locator(".book-scale-break")).toHaveCount(1);
  await page.getByLabel("Timeline start handle").focus(); await page.keyboard.press("ArrowRight");
  await expect(start).toHaveValue("1401");
  await end.fill("1600"); await end.press("Enter");
  await page.getByRole("button", { name: "Move range 1 year earlier", exact: true }).click();
  await expect(start).toHaveValue("1400");
  await expect(end).toHaveValue("1599");
  await start.fill("1100"); await start.press("Enter");
  await end.fill("1400"); await end.press("Enter");
  await expect(page.locator(".book-scale-break")).toHaveCount(1);
  // Periods include their end year; the final bucket must stay visible and
  // open the exact server-provided years after changing the scale.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/?popular=false");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  const lastPeriod = page.locator(".period-column").last();
  const [from, to] = (await lastPeriod.locator(".period-label").innerText()).split("–").map(Number);
  const last = (await lastPeriod.boundingBox())!;
  expect(last.width).toBeGreaterThan(0);
  const chart = (await page.locator(".period-chart").boundingBox())!;
  expect(last.x + last.width).toBeLessThanOrEqual(chart.x + chart.width + 1);
  await lastPeriod.focus(); await page.keyboard.press("Enter");
  await expect(page.getByLabel("End year", { exact: true })).toHaveValue(String(to));
  await expect(page.getByLabel("Start year", { exact: true })).toHaveValue(String(from === to ? from - 1 : from));
});
