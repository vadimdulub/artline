import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mockBooks } from "./books-fixture";

test.beforeEach(async ({ page }) => { await mockBooks(page); });

test("books heading and navigation fit desktop, tablet and phone widths", async ({ page }, testInfo) => {
  for (const width of [1440, 768, 640, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books");
    await expect(page.locator('ul[aria-label="Book index"] > li').first()).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath(`books-${width}.png`) });
    const bounds = await page.locator("h1").boundingBox();
    expect.soft(bounds!.x, `heading left at ${width}`).toBeGreaterThanOrEqual(0);
    expect.soft(bounds!.x + bounds!.width, `heading right at ${width}`).toBeLessThanOrEqual(width);
    expect.soft(await page.evaluate(() => document.documentElement.scrollWidth), `page overflow at ${width}`).toBeLessThanOrEqual(width);
    const links = page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link");
    for (const link of await links.all()) await expect.soft(link).toBeInViewport();
    await expect(page.getByRole("link", { name: "Painters", exact: true })).toBeVisible();
    const dark = await page.locator(".timeline-dark").boundingBox();
    if (width > 760) {
      expect.soft(dark!.height, `dark workspace height at ${width}`).toBeGreaterThan(650);
      expect.soft(dark!.y + dark!.height, `workspace fills screen at ${width}`).toBeCloseTo(900, 0);
      expect.soft((await page.locator(".timeline-stage").boundingBox())!.height).toBeGreaterThan(350);
    } else {
      const chart = page.getByRole("region", { name: "Books timeline", exact: true });
      expect.soft((await chart.boundingBox())!.height).toBeLessThanOrEqual(640);
      expect.soft(await chart.evaluate(el => el.scrollHeight > el.clientHeight)).toBe(true);
    }
  }
});

test("covers are only shown after opening a book, and their text remains readable", async ({ page }) => {
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books");
    await expect(page.locator('ul[aria-label="Book index"] > li').first()).toBeVisible();
    await expect(page.locator('[class*="coverTitle"]')).toHaveCount(0);
    await page.getByRole("button", { name: "Open Being and Nothingness by Jean-Paul Sartre", exact: true }).click();
    await expect(page.getByRole("dialog", { name: "Book details" })).toBeVisible();
    const clipped = await page.locator('[class*="coverTitle"], [class*="coverAuthor"], [class*="coverMark"]').evaluateAll(nodes => nodes.filter(node => {
      const element = node as HTMLElement;
      const bounds = element.getBoundingClientRect(), cover = element.parentElement!.getBoundingClientRect();
      return element.scrollHeight > element.clientHeight + 1 || element.scrollWidth > element.clientWidth + 1 || bounds.bottom > cover.bottom || bounds.right > cover.right;
    }).map(node => node.textContent));
    expect.soft(clipped, `clipped cover text at ${width}`).toEqual([]);
  }
});

test("books search combines with author filters and recovers from empty results", async ({ page }) => {
  await page.goto("/books");
  const search = page.getByLabel("Find a book or author");
  await search.fill("Homer");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(2);
  await page.locator("summary").filter({ hasText: "Authors" }).click();
  await page.getByRole("checkbox", { name: "Jean-Paul Sartre", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(0);
  await expect(page.getByText(/No books match/)).toBeVisible();
  await search.fill("Sartre");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Open Being and Nothingness by Jean-Paul Sartre", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await expect(search).toBeFocused();
  await expect(search).toHaveValue("");
  await expect(page.locator("summary").filter({ hasText: "Authors" })).toContainText("All authors");
  await expect(page.locator('summary[aria-label^="Collections:"]')).toHaveCount(0);
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
  await search.fill("no-such-book");
  await page.getByRole("button", { name: "Clear filters", exact: true }).first().focus();
  await page.keyboard.press("Enter");
  await expect(search).toBeFocused();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
});

test("books controls and text pass automated accessibility checks", async ({ page }) => {
  await page.goto("/books");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
  const all = page.getByLabel("Book start year");
  await all.hover();
  const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
  expect(scan.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => n.target) }))).toEqual([]);
});

test("books timeline uses BCE and plain years, follows filters, and opens book details by keyboard", async ({ page }, testInfo) => {
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/books");
    const timeline = page.getByRole("region", { name: "Books timeline", exact: true });
    await expect(timeline.getByRole("button")).toHaveCount(17);
    await expect(page.locator(".tick-row").getByText("BCE", { exact: true })).toBeVisible();
    await expect(page.locator(".tick-row").getByText("2000", { exact: true })).toBeVisible();
    await expect(page.locator(".tick-row").getByText("0 CE", { exact: true })).toHaveCount(0);
    const odyssey = timeline.getByRole("button", { name: /^The Odyssey,/ });
    await odyssey.focus();
    await page.keyboard.press("Enter");
    const drawer = page.getByRole("dialog", { name: "Book details", exact: true });
    await expect(drawer).toBeVisible();
    await expect(drawer.getByRole("heading", { name: "The Odyssey", exact: true })).toBeVisible();
    await expect(drawer.getByRole("heading", { name: "About this book", exact: true })).toBeVisible();
    await expect(drawer).toContainText("A long return becomes a meditation");
    await page.keyboard.press("Escape");
    await expect(drawer).toHaveCount(0);
    await expect(odyssey).toBeFocused();
    await expect(page.getByRole("heading", { name: "Books through time" })).toBeInViewport();
    await page.getByLabel("Book start year").fill("1700");
    await page.getByLabel("Book start year").press("Enter");
    await expect(timeline.getByRole("button")).toHaveCount(7);
    await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(7);
    await expect(page.locator('ul[aria-label="Book index"] > li').first()).toContainText("Faust");
    await page.getByLabel("Find a book or author").fill("Sartre");
    await expect(timeline.getByRole("button")).toHaveCount(1);
    await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
    await page.reload();
    await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
    await expect(page.getByLabel("Book start year")).toHaveValue("1700");
    await page.getByRole("button", { name: "Reset view", exact: true }).click();
    await expect(timeline.getByRole("button")).toHaveCount(17);
    await expect(page.getByLabel("Book start year")).toHaveValue("-5000");
    await expect(page.getByLabel("Book end year")).toHaveValue("2000");
    await page.getByLabel("Book start year").fill("-750");
    await page.getByLabel("Book start year").press("Enter");
    await expect(page.getByLabel("Book start year")).toHaveValue("-750");
    await page.getByLabel("Book end year").fill("-720");
    await page.getByLabel("Book end year").press("Enter");
    await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(3);
    await expect(timeline.getByRole("button", { name: /^The Odyssey,/ })).toContainText("c. 8th century BCE");
    await page.getByRole("button", { name: "Reset view", exact: true }).click();
    await expect(timeline.getByRole("button")).toHaveCount(17);
    await page.screenshot({ path: testInfo.outputPath(`timeline-${width}.png`), fullPage: false });
  }
});

test("books reject year zero and recover from a failed API request", async ({ page }) => {
  await page.goto("/books?start=0&end=2000");
  await expect(page.getByRole("alert").filter({ hasText: "no year zero" })).toBeVisible();
  await page.getByRole("button", { name: "Reset view", exact: true }).first().click();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
  await page.route("**/api/backend/v1/books?**", route => route.fulfill({ status: 503, json: { error: { message: "Books temporarily unavailable." } } }));
  await page.getByLabel("Find a book or author").fill("Homer");
  await expect(page.getByRole("alert").filter({ hasText: "Books temporarily unavailable." })).toBeVisible();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(0);
  await page.unroute("**/api/backend/v1/books?**");
  await page.getByRole("button", { name: "Retry", exact: true }).click();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(2);
});

test("shared book filters combine authors and keep BCE controls valid", async ({ page }) => {
  await page.goto("/books");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
  await page.locator("summary").filter({ hasText: "Authors" }).click();
  await page.getByRole("checkbox", { name: "Homer", exact: true }).check();
  await page.getByRole("checkbox", { name: "Jean-Paul Sartre", exact: true }).check();
  await page.keyboard.press("Escape");
  await expect(page.locator("summary").filter({ hasText: "Authors" })).toBeFocused();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(3);
  await expect(page.locator(".book-mark")).toHaveCount(3);
  await page.reload();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(3);
  await page.getByRole("button", { name: "Remove Author: Jean-Paul Sartre filter", exact: true }).click();
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(2);
  await page.getByLabel("Book end year").fill("-1");
  await page.getByLabel("Book end year").press("Enter");
  await page.getByRole("button", { name: "Move range 1 year later", exact: true }).click();
  await expect(page.getByLabel("Book start year")).toHaveValue("-4999");
  await expect(page.getByLabel("Book end year")).toHaveValue("1");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(2);
  expect(new URL(page.url()).searchParams.getAll("author")).toEqual(["Homer"]);
  await page.goto("/books?start=-1&end=20");
  await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(1);
  await page.getByLabel("Timeline start handle").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.getByLabel("Book start year")).toHaveValue("1");
  await expect(page.getByLabel("Timeline start handle")).toHaveAttribute("aria-valuetext", "1");
  await page.keyboard.press("ArrowLeft");
  await expect(page.getByLabel("Book start year")).toHaveValue("-1");
  await expect(page.getByLabel("Timeline start handle")).toHaveAttribute("aria-valuetext", "1 BCE");
});

// UI-only responses: these tests never create or change catalogue records.
test("painters timeline retains its layout and date controls after visiting Books", async ({ page }, testInfo) => {
  const artists = [
    { id: "ui-monet", slug: "claude-monet", name: "Claude Monet", start_year: 1840, end_year: 1926, date_display: "1840–1926", movement: { slug: "impressionism", name: "Impressionism", color: "#53745b" }, countries: ["FR"], artwork_count: 3, status: "review" },
    { id: "ui-pissarro", slug: "camille-pissarro", name: "Camille Pissarro", start_year: 1830, end_year: 1903, date_display: "1830–1903", movement: { slug: "impressionism", name: "Impressionism", color: "#53745b" }, countries: ["FR"], artwork_count: 3, status: "review" },
  ];
  await page.route("**/api/backend/v1/**", route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith("/timeline/facets")) return route.fulfill({ json: { countries: [], movements: [], regions: [] } });
    if (url.pathname.endsWith("/painters/options")) return route.fulfill({ json: { items: [], selected: [], has_more: false } });
    if (url.pathname.endsWith("/timeline")) {
      const items = artists.filter(artist => artist.name.toLowerCase().includes((url.searchParams.get("q") ?? "").toLowerCase()));
      return route.fulfill({ json: { mode: "individual", items, total: items.length, bins: [], periods: [], popular_only: true, range: { start: 1800, end: 1950 } } });
    }
    if (url.pathname.includes("/books")) return route.fallback();
    return route.fulfill({ status: 404, json: {} });
  });
  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/?start=1800&end=1950");
    await expect(page.locator(".artist-mark")).toHaveCount(2);
    const original = await page.locator(".timeline-dark").evaluate(el => ({ background: getComputedStyle(el).backgroundColor, width: el.getBoundingClientRect().width }));
    await page.getByRole("navigation", { name: "Primary navigation" }).getByRole("link", { name: "Books", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Books through time", exact: true })).toBeVisible();
    await expect(page.locator('ul[aria-label="Book index"] > li')).toHaveCount(17);
    expect(await page.locator(".timeline-dark").evaluate(el => ({ background: getComputedStyle(el).backgroundColor, width: el.getBoundingClientRect().width }))).toEqual(original);
    await page.goBack();
    await expect(page.locator(".artist-mark")).toHaveCount(2);
    expect(await page.locator(".timeline-dark").evaluate(el => ({ background: getComputedStyle(el).backgroundColor, width: el.getBoundingClientRect().width }))).toEqual(original);
    await page.keyboard.press("/");
    await expect(page.getByRole("searchbox")).toBeFocused();
    await page.getByRole("searchbox").fill("Monet");
    await expect(page.locator(".artist-mark")).toHaveCount(1);
    await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1800");
    await expect(page.getByLabel("End year", { exact: true })).toHaveValue("1950");
    await page.getByRole("button", { name: "Move range 1 year earlier" }).click();
    await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1799");
    await expect(page.getByLabel("End year", { exact: true })).toHaveValue("1949");
    await expect(page.getByRole("searchbox")).toHaveValue("Monet");
    await page.getByLabel("Timeline start handle").focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByLabel("Start year", { exact: true })).toHaveValue("1800");
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: testInfo.outputPath(`painters-${width}.png`) });
  }
});
