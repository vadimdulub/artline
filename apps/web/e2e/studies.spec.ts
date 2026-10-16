import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const caillebotte = "95e6574a-8509-4c70-ad3b-d22ed2cc1e83";
const monet = "cb33c32e-16ea-4d3e-9da0-287f5686585b";
const morisot = "8973b461-ce59-4e60-aad0-f6a361907f7a";
const seurat = "6b6a8026-124b-47d3-9533-89418fdb2c58";
// These are existing catalogue IDs, never database fixtures. All mutations in
// this suite require the loopback-only, in-memory member preview.
async function localPreview(page: Page) {
  const session = await (await page.request.get("/api/auth/session")).json();
  expect(session.local_debug).toBe(true);
}
async function createStudy(page: Page, title = "Paris and the modern city") {
  await localPreview(page);
  await page.goto("/studies");
  await page.getByRole("button", { name: "+ New study", exact: true }).click();
  await page.getByLabel("Study title", { exact: true }).fill(title);
  await page.getByRole("button", { name: "Create study", exact: true }).click();
  await expect(page).toHaveURL(/\/studies\/[a-f0-9-]{36}(?:\?|$)/);
  await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
  return new URL(page.url()).pathname.split("/").at(-1)!;
}
async function addReference(page: Page, id: string, body: unknown) {
  const response = await page.request.post(`/api/studies/${id}/records`, { data: body, headers: { Origin: new URL(page.url()).origin } });
  expect(response.ok(), await response.text()).toBe(true);
}

test("study search, selection, links, notes, comparison, filters and export", async ({ page }, info) => {
  test.setTimeout(120000);
  const errors: string[] = []; page.on("pageerror", error => errors.push(error.message));
  const id = await createStudy(page);
  await page.getByRole("button", { name: "+ Add records", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Add to your study", exact: true });
  await dialog.getByRole("searchbox", { name: "Search records" }).fill("Paris Street");
  await dialog.getByLabel("Artist or creator", { exact: true }).fill("Caillebotte");
  await dialog.getByLabel("With images").check();
  await dialog.getByLabel("Select Paris Street; Rainy Day", { exact: true }).check();
  await expect(dialog.getByRole("button", { name: "Add 1 record", exact: true })).toBeEnabled();
  await page.screenshot({ path: info.outputPath("01-add-dialog.png") });
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await dialog.getByRole("searchbox", { name: "Search records" }).fill("Normandy");
  await dialog.getByLabel("Artist or creator", { exact: true }).fill("Monet");
  await dialog.getByRole("checkbox", { name: /Select Arrival of the Normandy Train/ }).check();
  await dialog.getByRole("button", { name: "Add 2 records", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "2 of 2 records" })).toBeVisible();
  await addReference(page, id, { refs: [{ kind: "artwork", id: morisot }, { kind: "artwork", id: seurat }, { kind: "book", id: "wd-q1197590" }, { kind: "event", id: "event-q40415" }] });
  await page.reload();
  await expect(page.getByRole("status").filter({ hasText: "6 of 6 records" })).toBeVisible();
  await page.getByRole("button", { name: /^Paris Street; Rainy Day/ }).click();
  const inspector = page.getByRole("region", { name: "Record inspection", exact: true });
  await inspector.getByLabel("Your note").fill("=SUM(1,2)\nCompare the changing public street. <script>alert(1)</script>");
  await inspector.getByRole("button", { name: "Save note", exact: true }).click();
  await expect(inspector.getByRole("status")).toHaveText("Note saved.");
  await expect(page.getByLabel("Workflow", { exact: true })).toHaveCount(0);
  await expect(page.getByText(/Local preview.*Saved until the API restarts/)).toHaveCount(0);
  await page.screenshot({ path: info.outputPath("02-timeline-inspector.png") });
  await page.getByRole("button", { name: "Compare artworks", exact: true }).click();
  const comparison = page.getByRole("dialog", { name: "Compare artworks", exact: true });
  await comparison.getByLabel("Second artwork").selectOption(`artwork:${morisot}`);
  await expect(comparison.getByRole("heading", { name: "Woman at Her Toilette", exact: true })).toBeVisible();
  expect(await comparison.getByLabel("First artwork").inputValue()).toBe(`artwork:${caillebotte}`);
  await page.screenshot({ path: info.outputPath("03-comparison.png") });
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Compare artworks", exact: true })).toBeFocused();
  await inspector.getByRole("button", { name: "Close record", exact: true }).click();
  await page.getByLabel("From", { exact: true }).fill("1887"); await page.getByLabel("To", { exact: true }).fill("1887");
  await expect(page.getByRole("button", { name: /A Sunday on La Grande Jatte/ })).toHaveCount(0);
  await page.getByLabel("From", { exact: true }).fill("1900");
  await expect(page.locator("main").getByRole("alert")).toContainText("From must be earlier");
  await page.getByRole("button", { name: "Reset filters", exact: true }).first().click();
  await page.getByRole("button", { name: "Gallery", exact: true }).click();
  await page.getByRole("checkbox", { name: /Artworks/ }).uncheck();
  await expect(page.getByRole("status").filter({ hasText: "2 of 6 records" })).toBeVisible();
  await page.getByRole("searchbox", { name: "Search this study" }).fill("no matching record xyz");
  await expect(page.getByRole("heading", { name: "No records match these filters." })).toBeVisible();
  await page.getByRole("button", { name: "Reset filters", exact: true }).first().click();
  await page.getByRole("button", { name: "+ Add records", exact: true }).click();
  await dialog.getByRole("tab", { name: "Your own", exact: true }).click();
  await dialog.getByLabel("Record type", { exact: true }).selectOption("book");
  await dialog.getByLabel("Source URL", { exact: false }).fill("https://catalogue.bnf.fr/ark:/12148/cb31690619g");
  await dialog.getByLabel("Title", { exact: true }).fill("L’Assommoir — first book edition");
  await dialog.getByLabel("Author", { exact: true }).fill("Émile Zola");
  await dialog.getByLabel("Year", { exact: true }).fill("1877");
  await page.screenshot({ path: info.outputPath("04-your-link.png") });
  await dialog.getByRole("button", { name: "Add record", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "7 of 7 records" })).toBeVisible();
  await page.getByText("Export", { exact: true }).click();
  const download = page.waitForEvent("download"); await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  const file = await download; await file.saveAs(info.outputPath("study.csv"));
  const csv = await (await page.request.get(`/api/studies/${id}/export?format=csv`)).text();
  expect(csv).toContain("'=SUM(1,2)"); expect(csv).toContain("https://catalogue.bnf.fr/ark:/12148/cb31690619g");
  await page.reload(); await page.getByRole("button", { name: /Artwork Paris Street; Rainy Day/ }).click();
  await expect(inspector.getByLabel("Your note")).toHaveValue(/Compare the changing public street/);
  expect(errors).toEqual([]);
});

for (const width of [1440, 1024, 768, 390, 320]) test(`study and add dialog fit ${width}px with keyboard access`, async ({ page }, info) => {
  test.setTimeout(90000); await page.setViewportSize({ width, height: 900 });
  const id = await createStudy(page, `Study at ${width}px`);
  await addReference(page, id, { refs: [{ kind: "artwork", id: caillebotte }, { kind: "artwork", id: monet }] });
  await page.goto(`/studies/${id}`);
  if (width < 768) await expect(page.getByRole("button", { name: "Gallery", exact: true })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("status").filter({ hasText: "2 of 2 records" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({ path: info.outputPath(`gallery-${width}.png`) });
  await page.getByRole("button", { name: /Paris Street; Rainy Day/ }).click();
  if (width < 1280) { await expect(page.getByRole("dialog", { name: "Record inspection" })).toBeVisible(); await page.screenshot({ path: info.outputPath(`record-${width}.png`) }); await page.keyboard.press("Escape"); }
  else await page.getByRole("button", { name: "Close record", exact: true }).click();
  await page.getByRole("button", { name: "+ Add records", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Add to your study" });
  await dialog.getByRole("searchbox", { name: "Search records" }).fill("Monet");
  await expect(dialog.getByText("Searching…", { exact: true })).toHaveCount(0, { timeout: 10000 });
  await page.screenshot({ path: info.outputPath(`add-${width}.png`) });
  expect(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.keyboard.press("Escape"); await expect(page.getByRole("button", { name: "+ Add records", exact: true })).toBeFocused();
  await page.getByRole("button", { name: "Timeline", exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
});

test("expired sessions hide private study content and offer sign-in", async ({ page }) => {
  const id = await createStudy(page, "Private session check");
  await page.route("**/api/auth/session", route => route.fulfill({ json: { enabled: true, user: null } }));
  await page.evaluate(() => window.dispatchEvent(new Event("focus")));
  await expect(page.getByRole("heading", { name: "Sign in to your studies." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Private session check" })).toHaveCount(0);
  await expect(page.locator('form[action*="return_to"]')).toHaveAttribute("action", new RegExp(encodeURIComponent(`/studies/${id}`)));
});

test("bookmark picker, personal records without URLs and failed saves remain recoverable", async ({ page }) => {
  test.setTimeout(60000);
  const id = await createStudy(page, "Bookmark and recovery check");
  const origin = new URL(page.url()).origin;
  expect((await page.request.put(`/api/bookmarks/artwork/${caillebotte}`, { headers: { Origin: origin } })).ok()).toBe(true);
  await page.getByRole("button", { name: "+ Add records", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Add to your study" });
  await dialog.getByRole("tab", { name: "Bookmarks", exact: true }).click();
  await dialog.getByRole("searchbox", { name: "Search records" }).fill("Paris Street");
  await dialog.getByLabel("Select Paris Street; Rainy Day", { exact: true }).check();
  await dialog.getByRole("button", { name: "Add 1 record", exact: true }).click();
  await page.getByRole("button", { name: /Paris Street; Rainy Day/ }).click();
  const inspector = page.getByRole("region", { name: "Record inspection" });
  await page.route(`**/api/studies/${id}/records/artwork/${caillebotte}`, route => route.request().method() === "PUT" ? route.fulfill({ status: 503, json: { error: { message: "Your note could not be saved. Try again." } } }) : route.continue());
  await inspector.getByLabel("Your note").fill("Keep this draft when saving fails.");
  await inspector.getByRole("button", { name: "Save note", exact: true }).click();
  await expect(inspector.getByRole("alert")).toContainText("could not be saved");
  await expect(inspector.getByLabel("Your note")).toHaveValue("Keep this draft when saving fails.");
  await page.unroute(`**/api/studies/${id}/records/artwork/${caillebotte}`);
  await inspector.getByRole("button", { name: "Save note", exact: true }).click();
  await expect(inspector.getByRole("status")).toHaveText("Note saved.");
  await inspector.getByRole("button", { name: "Remove from study", exact: true }).click();
  await inspector.getByRole("button", { name: "Remove record", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "0 of 0 records" })).toBeVisible();
  await page.route("**/api/studies/search?**", route => route.fulfill({ status: 503, json: { error: { message: "Search unavailable. Try again." } } }));
  await page.getByRole("button", { name: "+ Add records", exact: true }).click();
  await expect(dialog.getByRole("alert")).toContainText("Search unavailable");
  await page.unroute("**/api/studies/search?**"); await dialog.getByRole("button", { name: "Try again", exact: true }).click();
  await expect(dialog.getByRole("checkbox").filter({ hasNot: page.locator(":disabled") }).first()).toBeVisible();
  await dialog.getByRole("tab", { name: "Your own", exact: true }).click();
  await dialog.getByLabel("Record type", { exact: true }).selectOption("book");
  await dialog.getByLabel("Title", { exact: true }).fill("My private book");
  await expect(dialog.getByRole("button", { name: "Add record", exact: true })).toBeDisabled();
  await dialog.getByLabel("Year", { exact: true }).fill("1875");
  await dialog.getByLabel("End year", { exact: true }).fill("1870");
  await expect(dialog.getByRole("alert")).toContainText("From must be earlier");
  await expect(dialog.getByRole("button", { name: "Add record", exact: true })).toBeDisabled();
  await dialog.getByLabel("End year", { exact: true }).fill("1880");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await dialog.getByRole("button", { name: "Add record", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "1 of 1 records" })).toBeVisible();
  const study = await (await page.request.get(`/api/studies/${id}`)).json();
  expect(study.items[0]).toMatchObject({ title: "My private book", personal: true, kind: "book", href: "", sources: [], date: "1875–1880", intervals: [{ start: 1875, end: 1880 }] });
});

test("many studies can be searched, sorted and paged without mixing projects", async ({ page }, info) => {
  test.setTimeout(90000);
  await localPreview(page);
  const origin = new URL(test.info().project.use.baseURL!).origin;
  const prefix = `Library check ${Date.now()}`;
  const ids: string[] = [];
  try {
    for (let i = 0; i < 31; i++) {
      const response = await page.request.post("/api/studies", { headers: { Origin: origin }, data: { title: `${prefix} ${String(i).padStart(2, "0")}` } });
      expect(response.ok()).toBe(true); ids.push((await response.json()).id);
    }
    await page.goto("/studies");
    const library = page.getByRole("region", { name: "Your research studies" });
    await page.getByRole("searchbox", { name: "Search your studies" }).fill(prefix);
    await page.getByLabel("Sort by", { exact: true }).selectOption("title");
    await expect(library.getByRole("status")).toContainText("31 of");
    await expect(library.getByRole("listitem")).toHaveCount(24);
    await expect(library.getByRole("heading").first()).toHaveText(`${prefix} 00`);
    await page.screenshot({ path: info.outputPath("study-library.png") });
    expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.getByRole("button", { name: "Next →", exact: true }).click();
    await expect(library.getByRole("listitem")).toHaveCount(7);
    await expect(library.getByRole("heading").first()).toHaveText(`${prefix} 24`);
    await page.getByRole("button", { name: "← Previous", exact: true }).click();
    await expect(library.getByRole("listitem")).toHaveCount(24);
    await page.getByLabel("Sort by", { exact: true }).selectOption("recent");
    await expect(library.getByRole("heading").first()).toHaveText(`${prefix} 30`);
    await page.getByRole("searchbox", { name: "Search your studies" }).fill(`${prefix} 03`);
    await expect(library.getByRole("listitem")).toHaveCount(1);
    await page.reload();
    await expect(page.getByRole("searchbox", { name: "Search your studies" })).toHaveValue(`${prefix} 03`);
    await expect(library.getByRole("listitem")).toHaveCount(1);
    await library.getByRole("link").click();
    await expect(page.getByRole("heading", { name: `${prefix} 03`, exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Study settings", exact: true }).click();
    const settings = page.getByRole("dialog", { name: "Study settings", exact: true });
    await expect(settings.getByRole("combobox")).toHaveCount(0);
    await settings.getByLabel("Study title", { exact: true }).fill(`${prefix} Renamed`);
    await settings.getByRole("button", { name: "Save changes", exact: true }).click();
    await expect(page.getByRole("heading", { name: `${prefix} Renamed`, exact: true })).toBeVisible();
    await page.goto(`/studies?q=${encodeURIComponent(prefix)}&sort=recent`);
    await expect(library.getByRole("heading").first()).toHaveText(`${prefix} Renamed`);
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
      await page.screenshot({ path: info.outputPath(`study-library-${width}.png`) });
      expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    }
    await page.getByRole("searchbox", { name: "Search your studies" }).fill(`${prefix} unmatched`);
    await expect(page.getByRole("heading", { name: "No studies found." })).toBeVisible();
    await page.getByRole("button", { name: "Show all studies", exact: true }).click();
    await expect(library.getByRole("listitem")).toHaveCount(24);
  } finally {
    for (const id of ids) await page.request.delete(`/api/studies/${id}`, { headers: { Origin: origin } });
  }
});
