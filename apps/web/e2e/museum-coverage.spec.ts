import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("Botticelli is discoverable by default and his uncertain dates lead to the Uffizi", async ({ page }) => {
  await page.goto("/?q=Botticelli");
  await expect(page.getByRole("checkbox", { name: "Top 100 painters" })).toBeChecked();
  await page.locator(".artist-mark").filter({ hasText: "Sandro Botticelli" }).click();
  const panel = page.getByRole("dialog", { name: "Painter details", exact: true });
  await expect(panel.getByRole("heading", { name: "Artworks by year", exact: true })).toBeVisible();
  await expect(panel.locator(".work-row").filter({ hasText: "Spring (Primavera)" })).toContainText("c. 1480");
  await expect(panel.locator(".work-row").filter({ hasText: "The Birth of Venus" })).toContainText("c. 1485");
  await panel.getByRole("combobox", { name: "Artwork year" }).selectOption("1480");
  await expect(panel.locator(".work-row").filter({hasText:"Spring (Primavera)"})).toHaveCount(1);
  await expect(panel.getByRole("region",{name:"Artworks grouped at 1480",exact:true})).toBeVisible();
  await panel.getByRole("navigation", { name: "Collections for these artworks" }).getByRole("link", { name: "Uffizi Galleries", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Uffizi Galleries", exact: true })).toBeVisible();
  await expect(page.locator('summary[aria-label="Painters: Sandro Botticelli"]')).toBeVisible();
  await expect(page.getByText("Florence, Italy", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open The Birth of Venus", exact: true })).toBeVisible();
});

test("museum highlights remain distinct from personal picks and show permission evidence", async ({ page }) => {
  await page.goto("/museums/uffizi");
  await expect(page.getByRole("button", { name: "Open The Birth of Venus", exact: true })).toBeVisible();
  const selection = page.getByRole("group", { name: "Artwork selection" });
  await selection.getByRole("button", { name: /Museum highlights/ }).click();
  await expect(page.getByRole("button", { name: "Open Santa Trinita Maestà", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open The Birth of Venus", exact: true })).toHaveCount(0);
  await selection.getByRole("button", { name: /My must-see works/ }).click();
  const open = page.getByRole("button", { name: "Open The Birth of Venus", exact: true });
  await expect(open).toBeVisible();
  await open.click();
  const panel = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
  await expect(panel.getByText("My must-see work", { exact: true })).toBeVisible();
  await expect(panel.getByText("Museum highlight", { exact: true })).toHaveCount(0);
  await expect(panel.getByRole("button", { name: /View larger/ })).toHaveCount(0);
  await panel.getByText("Artwork sources", { exact: true }).click();
  await expect(panel.getByText(/Image permission pending: the Uffizi/)).toBeVisible();
  await expect(panel.locator('a[href="https://www.uffizi.it/en/professional-services/publications"]')).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(open).toBeFocused();
});

test("Frida has a sourced Mexican museum highlight without an unlicensed image or display claim", async ({ page }) => {
  await page.goto("/museums/museo-de-arte-moderno-mexico?artist=frida-kahlo-q5588");
  await expect(page.getByText("Mexico City, Mexico", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Open The Two Fridas (Las dos Fridas)", exact: true }).click();
  const panel = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
  await expect(panel.getByRole("heading", { name: "The Two Fridas (Las dos Fridas)", exact: true })).toBeVisible();
  await expect(panel.getByText("1939", { exact: true })).toBeVisible();
  await expect(panel.getByText("Museum highlight", { exact: true })).toBeVisible();
  await expect(panel.getByRole("button", { name: /View larger/ })).toHaveCount(0);
  await panel.getByText("Artwork sources", { exact: true }).click();
  await expect(panel.getByText(/Image permission pending: no explicit reusable-image grant/)).toBeVisible();
  await page.keyboard.press("Escape");
  await page.getByText("More artwork filters", {exact:true}).click();
  await page.getByRole("combobox", { name: "Display", exact: true }).selectOption("on_view");
  await expect(page.getByRole("heading", { name: "No matching works are confirmed on view" })).toBeVisible();
});

test("the new museum record works on phones and passes accessibility checks", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/museums/uffizi?artist=sandro-botticelli-q5669");
    const open = page.getByRole("button", { name: "Open The Birth of Venus", exact: true });
    await expect(open).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    let scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await open.click();
    const panel = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
    await expect(panel.getByRole("heading", { name: "The Birth of Venus", exact: true })).toBeVisible();
    expect(await panel.evaluate(el => el.scrollWidth)).toBeLessThanOrEqual(width);
    scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: `../../docs/screenshots/uffizi-record-${width}.png` });
  }
});
