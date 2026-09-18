import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function settled(page: import("@playwright/test").Page, count: number, noun = "authors") {
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".timeline-counter")).toContainText(`${count.toLocaleString("en-GB")} ${noun} in this view`);
}

test("author checkbox preserves filters, groups creators once and restores history", async ({ page }) => {
  await page.goto("/books"); await settled(page, 100, "books");
  const toggle = page.getByRole("checkbox", { name: "Show author lifespans", exact: true });
  await expect(toggle).not.toBeChecked();
  await toggle.check(); await settled(page, 92);
  await expect(page.locator(".book-author-mark")).toHaveCount(87);
  await expect(page.getByRole("list", { name: "Author index", exact: true }).locator("li")).toHaveCount(92);
  await expect(page.getByRole("checkbox", { name: "Top 100 books", exact: true })).toBeChecked();
  await expect(page.locator(".book-mark")).toHaveCount(0);
  await page.reload(); await settled(page, 92); await expect(toggle).toBeChecked();
  await toggle.uncheck(); await settled(page, 100, "books");
  await page.goBack(); await settled(page, 92); await expect(toggle).toBeChecked();
  await page.getByRole("checkbox", { name: "Women authors", exact: true }).check(); await settled(page, 17);
  await expect(toggle).toBeChecked();
  await page.getByRole("button", { name: "Reset view", exact: true }).click();
  await settled(page, 100, "books"); await expect(toggle).not.toBeChecked();
});

test("author years use life dates and the drawer links back to the author's books", async ({ page }) => {
  await page.goto("/books?top100=false&author=Jean-Paul+Sartre&start=1900&end=1910");
  await settled(page, 0, "books");
  await page.getByRole("checkbox", { name: "Show author lifespans" }).check();
  await settled(page, 1);
  const mark = page.locator(".book-author-mark");
  await expect(mark).toHaveCount(1); await expect(mark).toContainText("1905–1980");
  await mark.focus(); await page.keyboard.press("Enter");
  const drawer = page.getByRole("dialog", { name: "Book author details", exact: true });
  await expect(drawer).toContainText("Jean-Paul Sartre");
  await expect(drawer.getByRole("link", { name: "Creator source" })).toHaveAttribute("href", /^https:\/\/www.wikidata.org\/wiki\/Q/);
  await drawer.getByRole("button", { name: "Show books by this author", exact: true }).click();
  await expect(drawer).not.toBeVisible();
  await expect(page.getByRole("checkbox", { name: "Show author lifespans" })).not.toBeChecked();
  await expect(page.locator(".book-mark").first()).toBeVisible();
  expect(new URL(page.url()).searchParams.get("author")).toBe("Jean-Paul Sartre");
  expect(new URL(page.url()).searchParams.has("start")).toBe(false);
});

test("Russian author membership reflects the cutoff and retains exact counts", async ({ page }) => {
  const response=await page.request.get("/api/backend/v1/books?view=authors&top100=false&language=Q7737");
  const data=await response.json();
  await page.goto("/books?view=authors&top100=false&language=Q7737"); await settled(page, data.total);
  await expect(page.locator(".book-author-mark")).toHaveCount(data.total-data.undatedTotal);
  await page.getByLabel("Author start year").fill("1900"); await page.getByLabel("Author start year").press("Tab");
  await page.getByLabel("Author end year").fill("1949"); await page.getByLabel("Author end year").press("Enter");
  const narrowed=await (await page.request.get("/api/backend/v1/books?view=authors&top100=false&language=Q7737&start=1900&end=1949")).json();
  await settled(page,narrowed.total);
  expect(new URL(page.url()).searchParams.get("language")).toBe("Q7737");
  await expect(page.getByRole("checkbox", { name: "Show author lifespans" })).toBeChecked();
});

test("BCE, incomplete and absent lifespans remain honest and accessible", async ({ page }) => {
  await page.goto("/books?view=authors&top100=false&author=Homer"); await settled(page, 1);
  await expect(page.locator(".book-author-mark")).toContainText("900 BCE");
  await expect(page.locator(".book-author-mark")).toContainText("701 BCE");
  await page.goto("/books?view=authors&top100=false&author=Margaret+Atwood"); await settled(page, 1);
  await expect(page.locator(".book-author-mark")).toContainText("Born 1939 · death not recorded");
  await page.getByRole("button", { name: "Open author Margaret Atwood", exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Book author details" })).toContainText("Not recorded");
  await page.keyboard.press("Escape");
  await page.goto("/books?view=authors"); await settled(page, 92);
  const response = await page.request.get("/api/backend/v1/books?view=authors&top100=true");
  const data = await response.json();
  const unplaced = data.authors.find((a: { startYear: number | null }) => a.startYear === null);
  await page.getByRole("button", { name: `Open author ${unplaced.name}`, exact: true }).click();
  await expect(page.getByRole("dialog", { name: "Book author details" })).toContainText(unplaced.lifespan);
});

test("author checkbox, marks and drawer fit desktop and phones", async ({ page }, testInfo) => {
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 950 });
    await page.goto("/books?view=authors"); await settled(page, 92);
    await expect(page.getByRole("checkbox", { name: "Show author lifespans" })).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const scan = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`authors-${width}.png`) });
    await page.locator(".book-author-mark").first().click();
    const drawer = page.getByRole("dialog", { name: "Book author details" });
    const box = (await drawer.boundingBox())!;
    expect(await drawer.evaluate(node => node.scrollWidth)).toBeLessThanOrEqual(box.width + 1);
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: testInfo.outputPath(`author-drawer-${width}.png`) });
    await page.keyboard.press("Escape");
    await expect(page.locator(".book-author-mark").first()).toBeFocused();
  }
});

test("author pages stay bounded and switching views clears their cursor", async ({ page }) => {
  await page.goto("/books?view=authors&top100=false"); await settled(page, 3374);
  const index = page.getByRole("list", { name: "Author index", exact: true });
  await expect(index.locator("li")).toHaveCount(100);
  const first = await index.locator("strong").allTextContents();
  await page.getByRole("button", { name: "Next authors", exact: true }).click(); await settled(page, 3374);
  await expect(index.locator("li")).toHaveCount(100);
  expect(await index.locator("strong").allTextContents()).not.toEqual(first);
  expect(new URL(page.url()).searchParams.has("after")).toBe(true);
  await page.getByRole("checkbox", { name: "Show author lifespans" }).uncheck(); await settled(page, 8685, "books");
  expect(new URL(page.url()).searchParams.has("after")).toBe(false);
});
