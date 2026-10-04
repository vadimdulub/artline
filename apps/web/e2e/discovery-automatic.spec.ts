import { expect, test } from "@playwright/test";

test("all movement choices are available before Top 100 is cleared; selection fits every matching painter", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("checkbox", { name: "Top 100 painters", exact: true })).toBeChecked();
  await page.locator("summary").filter({ hasText: "Movements" }).click();
  await page.getByRole("checkbox", { name: "Pre-Raphaelite Brotherhood", exact: true }).check();
  await page.getByRole("button", { name: "Done", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Top 100 painters", exact: true })).not.toBeChecked();
  await expect.poll(() => new URL(page.url()).searchParams.get("fit")).toBeNull();
  const response = await page.request.get("/api/backend/v1/timeline?start=1100&end=2000&popular=false&movement=pre-raphaelite-brotherhood");
  const data = await response.json();
  expect(data.total).toBeGreaterThan(0);
  await expect.poll(() => Number(new URL(page.url()).searchParams.get("start"))).toBe(data.matchedRange.start);
  expect(Number(new URL(page.url()).searchParams.get("end"))).toBe(data.matchedRange.end);
  // A deliberate manual range is never immediately replaced by auto-fitting.
  const from = page.getByLabel("Start year", { exact: true });
  await from.fill("1800"); await from.press("Enter");
  await expect.poll(() => new URL(page.url()).searchParams.get("start")).toBe("1800");
});

for (const example of [
  { path: "/books", search: "Find a book or author", checkbox: "Book highlights", q: "Tolstoy", endpoint: "books", bounds: "start=-5000&end=2000" },
  { path: "/events", search: "Find an event", checkbox: "Top 100 events", q: "Dunkirk", endpoint: "events", bounds: "start=-12000&end=2000" },
]) test(`${example.endpoint} search clears highlights and fits the full matching range`, async ({ page }) => {
  await page.goto(example.path);
  await expect(page.getByRole("checkbox", { name: example.checkbox, exact: true })).toBeChecked();
  await page.getByLabel(example.search, { exact: true }).fill(example.q);
  await expect(page.getByRole("checkbox", { name: example.checkbox, exact: true })).not.toBeChecked();
  const response = await page.request.get(`/api/backend/v1/${example.endpoint}?${example.bounds}&top100=false&q=${example.q}&limit=1`);
  const data = await response.json();
  expect(data.total).toBeGreaterThan(0);
  await expect.poll(() => new URL(page.url()).searchParams.get("fit")).toBeNull();
  await expect.poll(() => Number(new URL(page.url()).searchParams.get("start"))).toBe(data.matchedRange.start);
  expect(Number(new URL(page.url()).searchParams.get("end"))).toBe(data.matchedRange.end);
  // The user can explicitly turn the editorial selection back on.
  await page.getByRole("checkbox", { name: example.checkbox, exact: true }).check();
  await expect(page.getByRole("checkbox", { name: example.checkbox, exact: true })).toBeChecked();
});

test("All search clears every editorial cap and period changes fit the chosen context", async ({ page }) => {
  await page.goto("/all?type=artwork&highlights=true");
  await page.getByLabel("Search the timeline", { exact: true }).fill("Rossetti");
  await expect(page.getByRole("checkbox", { name: "Highlights", exact: true })).not.toBeChecked();
  await expect.poll(() => new URL(page.url()).searchParams.get("fit"), { timeout: 30000 }).toBeNull();
  const params = new URL(page.url()).searchParams;
  expect(params.get("artwork_popular")).toBe("false");
  expect(params.get("book_top100")).toBe("false");
  expect(params.get("event_top100")).toBe("false");
  expect(Number(params.get("start"))).toBeGreaterThan(1750);
  expect(Number(params.get("end"))).toBeLessThan(1971);
  await page.locator("summary").filter({ hasText: "Period or theme" }).click();
  await page.getByRole("radio", { name: "Romanticism", exact: true }).check();
  await expect(page.getByRole("checkbox", { name: "Highlights", exact: true })).not.toBeChecked();
  await expect.poll(() => new URL(page.url()).searchParams.get("fit"), { timeout: 30000 }).toBeNull();
  expect(Number(new URL(page.url()).searchParams.get("start"))).toBeGreaterThanOrEqual(1700);
});


test("Paintings search fits artwork creation dates independently of painter lifespans", async ({ page }) => {
  await page.goto("/?view=paintings");
  const search = page.locator('input[type="search"]').first();
  await search.fill("Rossetti");
  await expect(page.getByRole("checkbox", { name: "Top 100 painters", exact: true })).not.toBeChecked();
  await expect.poll(() => new URL(page.url()).searchParams.get("fit"), { timeout: 30000 }).toBeNull();
  const response = await page.request.get("/api/backend/v1/atlas?selection=true&type=artwork&start=1100&end=2000&highlights=false&artwork_image_only=true&artwork_popular=false&artwork_q=Rossetti");
  const data = await response.json();
  expect(data.total).toBeGreaterThan(0);
  await expect.poll(() => Number(new URL(page.url()).searchParams.get("start"))).toBe(data.matchedRange.start);
  expect(Number(new URL(page.url()).searchParams.get("end"))).toBe(data.matchedRange.end);
});
