import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

for (const width of [1440, 390]) {
  test(`Wikipedia descriptions and attribution are readable at ${width}px`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    const wikipediaRequests: string[] = [];
    page.on("request", request => { if (new URL(request.url()).hostname.endsWith("wikipedia.org")) wikipediaRequests.push(request.url()); });
    await page.goto("/events?event=event-q361");
    const panel = page.getByRole("dialog", { name: "Event details" });
    await expect(panel.getByRole("heading", { name: "First World War", exact: true })).toBeVisible();
    const description = panel.locator('section[aria-labelledby="event-about"] p');
    await expect(description).toContainText("global conflict between two coalitions");
    expect((await description.innerText()).length).toBeLessThanOrEqual(850);
    await expect(panel.getByRole("link", { name: "Wikipedia", exact: true })).toHaveAttribute("href", "https://en.wikipedia.org/wiki/World_War_I");
    await expect(panel.getByRole("link", { name: "CC BY-SA 4.0", exact: true })).toHaveAttribute("href", "https://creativecommons.org/licenses/by-sa/4.0/");
    await expect(panel).toContainText("contributors · Shortened excerpt");
    expect(wikipediaRequests).toEqual([]);
    expect((await new AxeBuilder({ page }).include("dialog").withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`description-${width}.png`) });
  });
}

test("a translated article has an English summary and its original source credit", async ({ page }) => {
  await page.goto("/events?event=event-q930351");
  const panel = page.getByRole("dialog");
  await expect(panel.getByRole("heading", { name: "Suomusjärvi culture", exact: true })).toBeVisible();
  await expect(panel.locator('section[aria-labelledby="event-about"] p')).not.toContainText("not yet been established");
  await expect(panel.getByRole("link", { name: "Russian Wikipedia", exact: true })).toHaveAttribute("href", /^https:\/\/ru\.wikipedia\.org\/wiki\//);
  await expect(panel.getByRole("link", { name: "CC BY-SA 4.0", exact: true })).toBeVisible();
  await expect(panel).toContainText("contributors · English summary");
  await expect(panel.locator('section[aria-labelledby="event-about"] p')).toContainText("stone axes");
});

test("unresolved source conflicts keep their original metadata description", async ({ page }) => {
  await page.goto("/events?event=event-q2812224");
  const panel = page.getByRole("dialog");
  await expect(panel.getByRole("link", { name: "Wikidata", exact: true })).toHaveAttribute("href", "https://www.wikidata.org/wiki/Q2812224");
  await expect(panel.getByRole("link", { name: "CC0", exact: true })).toBeVisible();
});

test("search includes the newly stored description", async ({ page }) => {
  const result = await page.request.get("/api/backend/v1/events?top100=true&q=coalitions");
  expect(result.ok()).toBe(true);
  const body = await result.json();
  expect(body.items.some((event: { id: string }) => event.id === "event-q361")).toBe(true);
  const detail = await page.request.get("/api/backend/v1/events/event-q361");
  const event = await detail.json();
  expect(event.descriptionSource.kind).toBe("wikipedia");
  expect(event.descriptionSource.revision).toBeGreaterThan(0);
  expect(event.startYear).toBe(1914); expect(event.endYear).toBe(1918); expect(event.top100).toBe(true);
});
