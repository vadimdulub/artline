import { expect, test } from "@playwright/test";

// Uses the real catalogue through read-only browser interactions.
for (const route of ["/?start=1800&end=1900", "/books?start=1700&end=1900", "/events?start=1700&end=1900", "/all?start=1700&end=1900"]) {
  test(`desktop full view gives ${route} more space without changing the selection`, async ({ page }, info) => {
    await page.goto(route);
    const frame = page.locator(".explorer");
    const canvas = frame.locator(":scope > .timeline-dark");
    const search = page.getByRole("searchbox").first();
    const fullView = page.getByRole("button", { name: "Full view", exact: true });
    await expect(fullView).toBeVisible();
    const before = (await canvas.boundingBox())!;
    const url = page.url();
    const searchBox = (await search.boundingBox())!;
    const buttonBox = (await fullView.boundingBox())!;
    // The entry control shares the search row instead of adding another row.
    expect(buttonBox.y).toBeLessThan(searchBox.y + searchBox.height);
    expect(buttonBox.y + buttonBox.height).toBeGreaterThan(searchBox.y);
    await fullView.click();
    await expect(frame).toHaveAttribute("data-full-view", "true");
    await expect(page.locator(".site-header")).toHaveJSProperty("inert", true);
    await expect(search).toBeHidden();
    const expanded = (await canvas.boundingBox())!;
    expect(expanded.height - before.height).toBeGreaterThan(80);
    expect(expanded.y).toBeLessThanOrEqual(46);
    await expect(page).toHaveURL(url);
    await page.screenshot({ path: info.outputPath("desktop-full-view.png") });

    const filters = page.getByRole("button", { name: "Filters", exact: true });
    await filters.click();
    await expect(search).toBeVisible();
    await page.getByRole("button", { name: "Close filters", exact: true }).click();
    await expect(search).toBeHidden();
    await expect(filters).toBeFocused();
    await page.keyboard.press("/");
    await expect(search).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(filters).toHaveAttribute("aria-expanded", "false");
    await page.keyboard.press("Escape");
    await expect(frame).toHaveAttribute("data-full-view", "false");
    await expect(fullView).toBeFocused();
    await expect(page.locator(".site-header")).toHaveJSProperty("inert", false);
    await expect(page.locator("body")).not.toHaveCSS("overflow", "hidden");
    await expect(search).toBeVisible();
    await expect(page).toHaveURL(url);
    expect((await canvas.boundingBox())!.height).toBe(before.height);
  });
}
