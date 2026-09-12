import { e2eEditorToken } from "./editor-token";
import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function expectSourceCount(page: Page, path = "/museums") {
  const response = await page.request.get(`/api/backend/v1${path}?${new URL(page.url()).searchParams}`);
  expect(response.ok()).toBe(true);
  const data = await response.json();
  const total = path.endsWith("/works") ? new Intl.NumberFormat("en-GB").format(data.total) : String(data.total);
  await expect(page.locator('[role="status"]').filter({hasText:/in this view|Finding collections|Finding artworks/}).first()).toContainText(total);
  return data;
}

test("museum regions and countries are physical locations and combine correctly", async ({ page }) => {
  await page.goto("/museums");
  await expectSourceCount(page);
  const regions = page.locator(".multi-filter").filter({ has: page.locator("summary", { hasText: "Regions" }) });
  await regions.locator("summary").click();
  await regions.getByRole("checkbox", { name: "Northern America", exact: true }).check();
  await regions.getByRole("checkbox", { name: "Northern Europe", exact: true }).check();
  await expectSourceCount(page);
  await regions.getByRole("button", { name: "Done", exact: true }).click();
  const countries = page.locator(".multi-filter").filter({ has: page.locator("summary", { hasText: "Countries" }) });
  await countries.locator("summary").click();
  await countries.getByRole("checkbox", { name: "Denmark", exact: true }).check();
  const danish = await expectSourceCount(page);
  expect(danish.total).toBeGreaterThan(0);
  expect(danish.items.every((museum: {venues: {country:string}[]}) => museum.venues.some(venue => venue.country === "DK"))).toBe(true);
  await countries.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Skagens Museum", exact: true })).toBeVisible();
  await page.reload();
  await expectSourceCount(page);
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await page.getByRole("combobox", { name: "Selection", exact: true }).selectOption("museum");
  await expectSourceCount(page);
  await page.getByRole("combobox", { name: "Display", exact: true }).selectOption("on_view");
  await expect(page.getByRole("heading", { name: "No collections match these filters" })).toBeVisible();
});

test("museum highlights open a right-hand artwork record, source links and nested viewer", async ({ page }) => {
  await page.goto("/museums/the-met?selection=museum&sort=curated&q=Self-Portrait&artist=rembrandt");
  await expectSourceCount(page,"/museums/the-met/works");
  const open = page.getByRole("button", { name: "Open Self-Portrait", exact: true });
  await open.click();
  const drawer = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
  await expect(drawer.getByRole("heading", { name: "Self-Portrait", exact: true })).toBeVisible();
  expect((await drawer.boundingBox())!.x).toBeGreaterThan(0);
  await expect(drawer.getByText("Display not verified.", { exact: false })).toBeVisible();
  await expect(drawer.getByRole("link", { name: /Designation source/ })).toHaveAttribute("href", /objects\/437397$/);
  await drawer.getByRole("button", { name: "View larger", exact: false }).click();
  await expect(page.locator(".image-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(drawer).toBeVisible();
  await expect(drawer.getByRole("button", { name: "View larger", exact: false })).toBeFocused();
  await page.screenshot({ path: "../../docs/screenshots/museum-artwork-desktop.png" });
  const savedURL = page.url();
  await page.keyboard.press("Escape");
  await expect(open).toBeFocused();
  await page.goto(savedURL);
  await expect(drawer.getByRole("heading", { name: "Self-Portrait", exact: true })).toBeVisible();
  await page.goBack();
  await expect(drawer).toHaveCount(0);
});

test("museum detail filters use artwork dates and never infer on-view from holdings", async ({ page }) => {
  await page.goto("/museums/the-met");
  await expectSourceCount(page,"/museums/the-met/works");
  const painters=page.locator('.multi-filter').filter({has:page.locator('summary[aria-label^="Painters:"]')});
  await painters.locator("summary").click();
  await painters.getByRole("searchbox",{name:"Search painters"}).fill("Rembrandt");
  await painters.getByRole("checkbox",{name:"Rembrandt van Rijn",exact:true}).check();
  await painters.getByRole("button",{name:"Done",exact:true}).click();
  await expectSourceCount(page,"/museums/the-met/works");
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await page.getByText("More artwork filters", { exact: true }).click();
  await page.getByLabel("Creation start year", { exact: true }).fill("1800");
  await expectSourceCount(page,"/museums/the-met/works");
  const venues=page.locator('.multi-filter').filter({has:page.locator('summary[aria-label^="Confirmed at venues:"]')});
  await venues.locator("summary").click();
  await venues.getByRole("checkbox",{name:"The Met Fifth Avenue",exact:true}).check();
  await venues.getByRole("button",{name:"Done",exact:true}).click();
  await expect(page.getByRole("heading", { name: "No matching works are confirmed on view" })).toBeVisible();
  await page.goto("/museums/hilma-af-klint-foundation");
  await expect(page.locator("summary", { hasText: "Exhibition information" })).toBeVisible();
  await expect(page.locator("summary", { hasText: "Visiting information" })).toHaveCount(0);
});

test("must-see editor protects unsaved notes and keeps rejected changes", async ({ page }) => {
  await page.goto("/museums/the-met?q=Self-Portrait&artist=rembrandt");
  await page.getByText("Edit my must-see list", { exact: true }).click();
  await page.getByLabel("Editor token", { exact: true }).fill(e2eEditorToken());
  await page.getByRole("button", { name: "Open Self-Portrait", exact: true }).click();
  const drawer = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
  await drawer.getByRole("checkbox", { name: "Include in my must-see works", exact: true }).check();
  await drawer.getByLabel("Why I want to see it", { exact: true }).fill("Compare the paint surface with the reproduction.");
  page.once("dialog", dialog => dialog.dismiss());
  await drawer.getByRole("button", { name: "Close artwork details", exact: true }).click();
  await expect(drawer).toBeVisible();
  await page.route("**/museums/the-met/must-see", route => route.fulfill({ status: 409, contentType: "application/json", body: JSON.stringify({ error: { message: "Selection changed. Reload before saving." } }) }));
  await drawer.getByRole("button", { name: "Save my selection", exact: true }).click();
  await expect(drawer.getByRole("alert")).toContainText("Selection changed");
  await expect(drawer.getByRole("textbox", { name: "Why I want to see it", exact: true })).toHaveValue("Compare the paint surface with the reproduction.");
  page.once("dialog", dialog => dialog.accept());
  await drawer.getByRole("button", { name: "Close artwork details", exact: true }).click();
  await expect(drawer).toHaveCount(0);
});

test("an invalid editor token can be cleared without leaving the museum", async ({ page }) => {
  await page.goto("/museums/the-met?q=Self-Portrait&artist=rembrandt");
  await expect(page.getByRole("button", { name: "Open Self-Portrait", exact: true })).toBeVisible();
  await page.getByText("Edit my must-see list", { exact: true }).click();
  await page.getByLabel("Editor token", { exact: true }).fill("invalid-test-token");
  const error = page.getByRole("main").getByRole("alert");
  await expect(error).toContainText("We couldn’t load this view");
  await expect(page.getByLabel("Editor token", { exact: true })).toHaveValue("invalid-test-token");
  await page.getByRole("button", { name: "Clear editor token", exact: true }).click();
  await expect(page.getByRole("button", { name: "Open Self-Portrait", exact: true })).toBeVisible();
  await expect(error).toHaveCount(0);
});

test("museum screens and artwork drawer fit phones and pass accessibility checks", async ({ page }) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/museums");
    await expectSourceCount(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    let scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: `../../docs/screenshots/museums-${width}.png` });
    await page.goto("/museums/the-met?q=Self-Portrait&artist=rembrandt");
    await expect(page.getByRole("button", { name: "Open Self-Portrait", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: `../../docs/screenshots/museum-met-${width}.png`, fullPage: true });
    scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.getByRole("button", { name: "Open Self-Portrait", exact: true }).click();
    const drawer = page.getByRole("dialog", { name: "Museum artwork details", exact: true });
    await expect(drawer.getByRole("heading", { name: "Self-Portrait", exact: true })).toBeVisible();
    expect(await drawer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(width);
    scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
  }
});
