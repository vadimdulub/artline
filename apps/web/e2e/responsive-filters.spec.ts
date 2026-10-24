import { expect, test, type Locator, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mockResponsiveFilters } from "./responsive-filter-fixture";

type Choice = [label: string, key: string, name: string, value: string, kind?: "radio"];
type Select = [label: string, key: string, value: string];
type Surface = { name: string; route: string; choices?: Choice[]; toggles?: [label: string, key: string][]; selects?: Select[]; reset?: string; submit?: boolean };
const artChoices: Choice[] = [["Painters", "painter", "Claude Monet", "claude-monet"], ["Movements", "movement", "Impressionism", "impressionism"], ["Regions", "region", "Europe", "europe"], ["Countries", "country", "France", "FR"]];
const bookChoices: Choice[] = [["Authors", "author", "Leo Tolstoy", "Leo Tolstoy"], ["Regions", "region", "Europe", "europe"], ["Countries", "country", "France", "FR"], ["Languages", "language", "French", "french"]];
const eventChoices: Choice[] = [["Topics", "topic", "Politics", "Politics"], ["Types", "kind", "Event", "Event"], ["Regions", "region", "Europe", "Europe"], ["Countries", "country", "France", "France"]];
const surfaces: Surface[] = [
  { name: "painters", route: "/?start=1800&end=1950", choices: artChoices, toggles: [["Women artists", "women"], ["Top 100 painters", "popular"]] },
  { name: "books", route: "/books", choices: bookChoices, toggles: [["Women authors", "women"], ["Book highlights", "top100"]] },
  { name: "events", route: "/events", choices: eventChoices, toggles: [["Top 100 events", "top100"]] },
  { name: "all", route: "/all?preset=renaissance", choices: [["Period or theme", "preset", "The Renaissance", "renaissance", "radio"], ["Creators", "creator", "Claude Monet · Painter", "painter:claude-monet"], ["Continents", "continent", "Europe", "europe"], ["Countries", "country", "France", "FR"]], toggles: [["Highlights", "highlights"]], selects: [["Region", "region", "europe"]], reset: "Show starting points" },
  { name: "artists", route: "/artists", choices: [["Countries", "country", "France", "FR", "radio"], ["Movements", "movement", "Impressionism", "impressionism", "radio"]], toggles: [["Top 1,000 cohort", "popular"], ["Women artists", "women"]], selects: [["Order", "sort", "name"]] },
  { name: "museums", route: "/museums", choices: artChoices.map(([label, key, name, value]) => [label, key === "painter" ? "artist" : key, name, value]), selects: [["Selection", "selection", "museum"], ["Display", "display", "on_view"]] },
  { name: "collection", route: "/museums/national-gallery", choices: [["Painters", "artist", "Claude Monet", "claude-monet"], ["Movements", "movement", "Impressionism", "impressionism"]], toggles: [["With pictures", "image_only"]] },
  { name: "artworks", route: "/artworks", toggles: [["Undated works", "undated"], ["With pictures", "image_only"]] },
  { name: "exhibitions", route: "/exhibitions", selects: [["Format", "format", "physical"], ["Event record", "state", "held"]], submit: true },
];
const widths = [320, 390, 430, 760, 761, 768, 1024, 1440];

test.beforeEach(async ({ page }) => { await mockResponsiveFilters(page); });

async function openFilters(page: Page, scope = page.locator(".atlas-filter-system").first()) {
  const toggle = scope.getByRole("button", { name: "Filters", exact: true });
  await expect(async () => {
    if (await toggle.isVisible() && await toggle.getAttribute("aria-expanded") === "false") await toggle.click();
    await expect(scope.locator(".search-field input")).toBeVisible({ timeout: 1000 });
  }).toPass({ timeout: 10000 });
  return scope;
}
function picker(scope: Locator, label: string) {
  return scope.locator(".multi-filter").filter({ has: scope.page().locator(`summary[aria-label^="${label}:"]`) });
}
async function fits(page: Page, element: Locator, width: number) {
  await expect(async () => {
    const box = (await element.boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(-1);
    expect(box.x + box.width).toBeLessThanOrEqual(width + 1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }).toPass({ timeout: 2000 });
}
async function apply(page: Page, surface: Surface) {
  if (surface.submit) {
    await page.getByRole("button", { name: "Search", exact: true }).click();
    await expect(page.getByRole("form", { name: "Filter exhibitions" })).toHaveAttribute("aria-busy", "false");
  }
}

for (const surface of surfaces) for (const width of widths) {
  test(`${surface.name}: filter geometry and every panel at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    const errors: string[] = [];
    page.on("pageerror", error => errors.push(error.message));
    await page.goto(surface.route);
    const scope = page.locator(".atlas-filter-system").first();
    if (width <= 760) {
      await expect(scope.getByRole("button", { name: "Filters", exact: true })).toHaveAttribute("aria-expanded", "false");
      expect((await scope.boundingBox())!.height).toBeLessThanOrEqual(48);
    }
    await openFilters(page, scope);
    await fits(page, scope, width);
    const insets = await scope.locator(".atlas-filter-row>.multi-filter>summary,.all-period-filter>.multi-filter>summary,.atlas-filter-row>.atlas-select,.atlas-filter-row>.popular-filter-control").evaluateAll(cells => cells.map(cell => getComputedStyle(cell).paddingLeft));
    expect(new Set(insets).size).toBeLessThanOrEqual(1);
    const fields = scope.locator(".atlas-select :is(input,select), .search-field input");
    for (const field of await fields.all()) {
      await fits(page, field, width);
      const style = await field.evaluate(el => ({ font: parseFloat(getComputedStyle(el).fontSize), height: el.getBoundingClientRect().height }));
      expect(style.font).toBeGreaterThanOrEqual(width <= 760 ? 16 : 13);
      expect(style.height).toBeGreaterThanOrEqual(width <= 760 ? 44 : 18);
    }
    for (const [label] of surface.choices ?? []) {
      const control = picker(scope, label), summary = control.locator("summary");
      await summary.click();
      await expect(control.locator(".filter-checkboxes input").first()).toBeVisible();
      const panel = control.locator(".multi-filter-panel");
      await fits(page, panel, width);
      const labels = panel.locator(".filter-checkboxes label");
      for (const option of await labels.all()) {
        expect(await option.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
        if (width <= 760) expect((await option.boundingBox())!.height).toBeGreaterThanOrEqual(44);
      }
      await control.getByRole("searchbox").focus();
      await page.keyboard.press("Escape");
      await expect(control).not.toHaveAttribute("open");
      await expect(summary).toBeFocused();
    }
    if (surface.submit) {
      // Text, numeric and select controls must share the same field treatment.
      const fieldStyles = await scope.locator(".atlas-select input, .atlas-select select").evaluateAll(fields => fields.map(el => {
        const s = getComputedStyle(el);
        return { height: el.getBoundingClientRect().height, font: s.fontSize, border: s.borderTopWidth, background: s.backgroundColor };
      }));
      expect(new Set(fieldStyles.map(style => JSON.stringify(style))).size).toBe(1);
    }
    if ([320, 768, 1440].includes(width)) await page.screenshot({ path: info.outputPath(`${surface.name}-${width}.png`) });
    expect(errors).toEqual([]);
  });
}

for (const surface of surfaces) for (const width of [390, 1440]) {
  test(`${surface.name}: all choices, switches, search and reset at ${width}px`, async ({ page }) => {
    const requests: URL[] = [];
    page.on("request", request => { if (request.url().includes("/api/backend/v1/")) requests.push(new URL(request.url())); });
    await page.setViewportSize({ width, height: 900 });
    await page.goto(surface.route);
    let scope = await openFilters(page);
    for (const [label, key, name, value, kind] of surface.choices ?? []) {
      const control = picker(scope, label);
      await control.locator("summary").click();
      await control.getByRole(kind ?? "checkbox", { name, exact: true }).check();
      await control.getByRole("button", { name: "Done", exact: true }).click();
      await expect.poll(() => new URL(page.url()).searchParams.getAll(key)).toContain(value);
      await expect.poll(() => requests.some(url => url.searchParams.getAll(key).includes(value))).toBe(true);
      await expect(control.locator("summary")).toContainText(name);
    }
    for (const [label, key] of surface.toggles ?? []) {
      const control = scope.getByRole("checkbox", { name: label, exact: true });
      const before = await control.isChecked();
      await control.setChecked(!before);
      await expect(control).toBeChecked({ checked: !before });
      await expect.poll(() => new URL(page.url()).searchParams.get(key)).not.toBeNull();
    }
    for (const [label, key, value] of surface.selects ?? []) {
      await scope.getByRole("combobox", { name: label, exact: true }).selectOption(value);
      await apply(page, surface);
      await expect.poll(() => new URL(page.url()).searchParams.get(key)).toBe(value);
      scope = await openFilters(page);
    }
    // Searching the timelines deliberately leaves the highlight cohort and fits
    // the date range. Explicit dimensions must survive that documented change.
    const autoScope = ["painters", "books", "events", "all"].includes(surface.name) ? ["fit", "start", "end", "popular", "top100", "highlights", "artwork_popular", "book_top100", "event_top100"] : [];
    const selection = () => [...new URL(page.url()).searchParams].filter(([key]) => !autoScope.includes(key)).sort();
    const selected = selection();
    await scope.locator(".search-field input").fill("Monet");
    await apply(page, surface);
    await expect.poll(() => new URL(page.url()).searchParams.get("q")).toBe("Monet");
    scope = await openFilters(page);
    await scope.getByRole("button", { name: /^Clear (search|find)/i }).click();
    await apply(page, surface);
    await expect.poll(() => new URL(page.url()).searchParams.get("q")).toBeNull();
    expect(selection()).toEqual(selected);
    await page.reload();
    scope = await openFilters(page);
    for (const [label, , name] of surface.choices ?? []) await expect(picker(scope, label).locator("summary")).toContainText(name);
    for (const [label, , value] of surface.selects ?? []) await expect(scope.getByRole("combobox", { name: label, exact: true })).toHaveValue(value);
    const removed = surface.choices?.at(-1);
    if (removed) {
      await page.getByRole("button", { name: `Remove ${removed[2]} filter`, exact: true }).click();
      await expect.poll(() => new URL(page.url()).searchParams.getAll(removed[1])).toHaveLength(0);
      for (const [, key, , value] of surface.choices!.slice(0, -1)) expect(new URL(page.url()).searchParams.getAll(key)).toContain(value);
    }
    await scope.getByRole("button", { name: surface.reset ?? "Reset view", exact: true }).click();
    await expect.poll(() => new URL(page.url()).searchParams.has("q")).toBe(false);
    for (const [, key] of [...(surface.choices ?? []), ...(surface.selects ?? [])]) await expect.poll(() => new URL(page.url()).searchParams.getAll(key)).toHaveLength(0);
    for (const [, key] of surface.toggles ?? []) expect(new URL(page.url()).searchParams.get(key)).not.toBe("true");
    await fits(page, page.locator(".atlas-filter-system").first(), width);
  });
}

for (const surface of surfaces) {
  test(`${surface.name}: resizing preserves focus and Escape restores the filter trigger`, async ({ page }) => {
    await page.setViewportSize({ width: 1024, height: 900 });
    await page.goto(surface.route);
    const scope = await openFilters(page), search = scope.locator(".search-field input");
    await search.focus();
    await expect(scope).toHaveAttribute("data-expanded", "true");
    await page.setViewportSize({ width: 390, height: 700 });
    await expect(search).toBeVisible();
    await expect(search).toBeFocused();
    await page.keyboard.press("Escape");
    const toggle = scope.getByRole("button", { name: "Filters", exact: true });
    await expect(toggle).toBeFocused();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");
    await page.keyboard.press("/");
    await expect(search).toBeVisible();
    await expect(search).toBeFocused();
    await scope.getByRole("button", { name: "Close filters", exact: true }).click();
    await expect(toggle).toBeFocused();
  });
  for (const width of [320, 1440]) test(`${surface.name}: accessible open filters at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(surface.route);
    const scope = await openFilters(page);
    if (surface.choices?.length) await picker(scope, surface.choices[0][0]).locator("summary").click();
    expect((await new AxeBuilder({ page }).include(".atlas-filter-system").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  });
}

for (const [type, name] of [["Painters", "Claude Monet"], ["Artworks", "Mona Lisa"], ["Books", "Utopia"], ["Events", "Council of Trent"]]) {
  for (const width of [320, 390, 760, 768, 1440]) test(`${type} layer: search and visibility controls fit at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/all?preset=renaissance&canvas=map");
    await expect(page.locator(".map-workspace-v2")).toHaveAttribute("aria-busy", "false");
    const layers = page.getByRole("button", { name: "Layers", exact: true });
    await layers.click();
    const panel = page.getByRole("complementary", { name: "Map layers", exact: true });
    const control = picker(panel, type);
    await control.locator("summary").click();
    const search = control.getByRole("searchbox", { name: `Search ${type.toLowerCase()}`, exact: true });
    await expect(search).toBeFocused();
    if (width <= 760) expect(await search.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
    await search.fill(name);
    const choice = control.getByRole("checkbox", { name: type === "Painters" ? name : `Show ${name}`, exact: true });
    await expect(choice).toBeVisible();
    const checked = await choice.isChecked();
    await choice.setChecked(!checked);
    await expect(choice).toBeChecked({ checked: !checked });
    if (type === "Painters") await expect(page).toHaveURL(/artwork_painter=claude-monet/);
    else await expect(page).toHaveURL(/map_hide=/);
    await fits(page, control.locator(".multi-filter-panel"), width);
    const panelBox = (await control.locator(".multi-filter-panel").boundingBox())!, containerBox = (await panel.boundingBox())!;
    expect(Math.abs(panelBox.x - containerBox.x)).toBeLessThanOrEqual(1);
    expect(Math.abs(panelBox.width - containerBox.width)).toBeLessThanOrEqual(1);
    const visibility = panel.getByRole("checkbox", { name: `Show ${type.toLowerCase()}`, exact: true });
    if (type !== "Painters") {
      await visibility.uncheck();
      await expect(search).toBeVisible();
      await expect(choice).toBeDisabled();
      await visibility.check();
      await expect(choice).toBeEnabled();
    }
    await control.getByRole("button", { name: `Clear search ${type.toLowerCase()}`, exact: true }).click();
    await expect(search).toBeFocused();
    await expect(control).toHaveAttribute("open");
    await search.fill(name);
    await page.screenshot({ path: info.outputPath(`layer-${type}-${width}.png`) });
    await panel.getByRole("button", { name: "Back to layers", exact: true }).click();
    await expect(control.locator("summary")).toBeVisible();
    await panel.getByRole("button", { name: "Close layers", exact: true }).click();
    await expect(layers).toBeFocused();
  });
}

for (const [route, label] of [["/", "About the popular painter selection"], ["/books", "About the book highlights"], ["/events", "About the Top 100 event selection"]]) {
  for (const width of [320, 768, 1440]) test(`filter help fits and dismisses at ${width}px on ${route}`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(route);
    const scope = await openFilters(page);
    const button = scope.getByRole("button", { name: label, exact: true });
    if (width <= 760) expect((await button.boundingBox())!.width).toBeGreaterThanOrEqual(44);
    await button.click();
    const tip = scope.getByRole("tooltip");
    await expect(tip).toBeVisible();
    await fits(page, tip, width);
    // WebKit deliberately does not focus buttons on pointer activation.
    await button.focus();
    await page.keyboard.press("Escape");
    await expect(tip).toBeHidden();
    await expect(button).toBeFocused();
    await expect(scope.locator(".search-field input")).toBeVisible();
  });
}

for (const surface of surfaces.slice(0, 4)) for (const [width, height] of [[320, 568], [740, 390]]) {
  test(`${surface.name}: full-view filters remain reachable at ${width}×${height}`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto(surface.route);
    await page.getByRole("button", { name: "Full view", exact: true }).click();
    const scope = await openFilters(page);
    expect((await scope.boundingBox())!.height).toBeLessThanOrEqual(height);
    if (surface.choices?.length) {
      const control = picker(scope, surface.choices.at(-1)![0]);
      await control.locator("summary").click();
      await control.getByRole("searchbox").focus();
      await page.keyboard.press("Escape");
      await expect(control).not.toHaveAttribute("open");
      await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "true");
    }
    await scope.getByRole("button", { name: "Close filters", exact: true }).click();
    await expect(scope.getByRole("button", { name: "Filters", exact: true })).toBeInViewport();
    await expect(page.locator(".range-track")).toBeInViewport();
    await page.keyboard.press("Escape");
    await expect(page.locator(".explorer")).toHaveAttribute("data-full-view", "false");
  });
}

test("museum secondary filters keep date and unknown-date selections exclusive", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/museums/national-gallery");
  const collection = page.getByRole("tabpanel", { name: "Collection", exact: true });
  await collection.getByText("More artwork filters", { exact: true }).click();
  const more = collection.locator("details").filter({ has: page.locator("summary").filter({ hasText: "More artwork filters" }) });
  await more.getByRole("combobox", { name: "Display", exact: true }).selectOption("on_view");
  for (const [label, name, key, value] of [["Confirmed at venues", "Main gallery", "venue", "venue"], ["Work types", "painting", "work_type", "painting"]]) {
    const control = picker(more, label);
    await control.locator("summary").click();
    await control.getByRole("checkbox", { name, exact: true }).check();
    await fits(page, control.locator(".multi-filter-panel"), 390);
    await control.getByRole("button", { name: "Done", exact: true }).click();
    expect(new URL(page.url()).searchParams.get(key)).toBe(value);
  }
  await more.getByRole("spinbutton", { name: "Creation start year" }).fill("1800");
  await more.getByRole("spinbutton", { name: "Creation end year" }).fill("1900");
  expect(new URL(page.url()).searchParams.get("start")).toBe("1800");
  expect(new URL(page.url()).searchParams.get("end")).toBe("1900");
  await more.getByRole("checkbox", { name: "Only unknown creation dates" }).check();
  expect(new URL(page.url()).searchParams.has("start")).toBe(false);
  expect(new URL(page.url()).searchParams.has("end")).toBe(false);
  await more.getByRole("spinbutton", { name: "Creation start year" }).fill("1850");
  expect(new URL(page.url()).searchParams.has("unknown_date")).toBe(false);
});

test("exhibition text and year filters apply together and survive reload", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/exhibitions");
  const scope = await openFilters(page);
  for (const [label, value] of [["Country", "France"], ["City", "Paris"], ["From year", "1800"], ["To year", "1989"]]) await scope.getByLabel(label, { exact: true }).fill(value);
  await scope.locator(".search-field input").fill("Monet");
  await scope.getByRole("button", { name: "Search", exact: true }).click();
  await expect(page).toHaveURL(/country=France/);
  await page.reload();
  await openFilters(page);
  for (const [label, value] of [["Country", "France"], ["City", "Paris"], ["From year", "1800"], ["To year", "1989"]]) await expect(scope.getByLabel(label, { exact: true })).toHaveValue(value);
  await expect(scope.locator(".search-field input")).toHaveValue("Monet");
});

for (const surface of surfaces) for (const width of [320, 1440]) {
  test(`${surface.name}: long queries and removable chips fit at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const query = "Études資料".repeat(25).slice(0, 200);
    const url = new URL(surface.route, "http://127.0.0.1");
    url.searchParams.set("q", query);
    await page.goto(url.pathname + url.search);
    const scope = await openFilters(page);
    await expect(scope.locator(".search-field input")).toHaveValue(query);
    await fits(page, scope, width);
    if (width === 320) {
      await scope.getByRole("button", { name: "Close filters", exact: true }).click();
      expect(new URL(page.url()).searchParams.get("q")).toBe(query);
      await openFilters(page);
    }
    const remove = page.getByRole("button", { name: /^Remove (Search|Title):/ });
    if (await remove.count()) {
      await remove.click();
      await expect.poll(() => new URL(page.url()).searchParams.has("q")).toBe(false);
      if (width === 320 && !surface.submit) {
        // A museum's secondary disclosure sits between its shell and chips.
        // Focus must still reach the shell when the final chip disappears.
        const remaining = page.locator(".active-filters button");
        if (!await remaining.count()) await expect(scope.getByRole("button", { name: "Filters", exact: true })).toBeFocused();
      }
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  });
}

for (const width of [320, 390, 1440]) test(`long creator choices wrap and empty searches recover at ${width}px`, async ({ page }) => {
  const longName = "A".repeat(200);
  await page.route("**/api/backend/v1/painters/options?**", route => route.fulfill({ json: { items: [{ slug: "long-name", name: longName }], selected: [], has_more: false } }));
  await page.setViewportSize({ width, height: 900 });
  await page.goto("/");
  const scope = await openFilters(page), painters = picker(scope, "Painters");
  await painters.locator("summary").click();
  const option = painters.locator(".filter-checkboxes label").filter({ hasText: longName });
  await expect(option).toBeVisible();
  expect(await option.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await painters.getByRole("checkbox", { name: longName, exact: true }).check();
  await painters.getByRole("button", { name: "Done", exact: true }).click();
  await fits(page, scope, width);
  const countries = picker(scope, "Countries");
  await countries.locator("summary").click();
  const search = countries.getByRole("searchbox", { name: "Search countries", exact: true });
  await search.fill("no-such-country");
  await expect(countries.getByText("No matches. Try another spelling or clear the search.")).toBeVisible();
  await countries.getByRole("button", { name: "Clear search countries", exact: true }).click();
  await expect(search).toBeFocused();
  await expect(countries.getByRole("checkbox", { name: "France", exact: true })).toBeVisible();
});

test("unavailable filter choices retry without losing the query", async ({ page }) => {
  let attempts = 0;
  await page.route("**/api/backend/v1/timeline/facets?**", route => ++attempts === 1
    ? route.fulfill({ status: 503, json: { error: { message: "Temporarily unavailable" } } }) : route.fallback());
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/?q=Monet");
  const scope = await openFilters(page), countries = picker(scope, "Countries");
  await countries.locator("summary").click();
  await page.getByRole("button", { name: "Retry filters", exact: true }).click();
  await expect(page.getByRole("button", { name: "Retry filters", exact: true })).toHaveCount(0);
  await countries.locator("summary").click();
  await expect(countries.getByRole("checkbox", { name: "France", exact: true })).toBeVisible();
  await expect(scope.locator(".search-field input")).toHaveValue("Monet");
});

for (const [name, route] of [["painters", "/?canvas=map&start=1800&end=1900"], ["books", "/books?canvas=map&start=1800&end=1900"], ["events", "/events?canvas=map&start=1800&end=1900"], ["all", "/all?canvas=map&preset=renaissance&start=1800&end=1900"]]) {
  for (const width of [390, 1440]) test(`${name} map: compact filters retain the period at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(route);
    const scope = page.locator(".atlas-filter-system").first();
    await expect(scope.getByRole("button", { name: "Filters", exact: true })).toBeVisible();
    await openFilters(page);
    await fits(page, scope, width);
    const control = scope.locator(".multi-filter").first();
    await control.locator("summary").click();
    await expect(control.locator(".multi-filter-panel")).toHaveCSS("position", "relative");
    await control.getByRole("searchbox").focus();
    await page.keyboard.press("Escape");
    await scope.getByRole("button", { name: "Close filters", exact: true }).click();
    expect(new URL(page.url()).searchParams.get("start")).toBe("1800");
    expect(new URL(page.url()).searchParams.get("end")).toBe("1900");
    await expect(scope.getByRole("button", { name: "Filters", exact: true })).toBeFocused();
  });
}
