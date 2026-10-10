import { expect, test, type Page } from "@playwright/test";
import type { EventsResponse } from "../lib/events";
import type { TimelineResponse } from "../lib/types";

const range = { start: 1900, end: 1909 };
const cases = [
  { view: "events", action: "button", key: "topic", value: "Science" },
  { view: "events", action: "column", key: "country", value: "France" },
  { view: "painters", action: "button", key: "country", value: "FR" },
  { view: "painters", action: "column", key: "movement", value: "impressionism" },
  { view: "painters", action: "index", key: "country", value: "FR" },
] as const;

async function settled(page: Page, total: number, noun: string) {
  await expect(page.locator(".timeline-counter")).toHaveText(`${total} ${noun} in this view`);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
}

// Browser-only responses; no catalogue or member database fixtures.
for (const example of cases) test(`${example.view} ${example.action} suggestion preserves the selected interval`, async ({ page }) => {
  const events = example.view === "events";
  const endpoint = events ? "events" : "timeline";
  const requests: URLSearchParams[] = [];
  await page.route(`**/api/backend/v1/${endpoint}/facets?*`, route => route.fulfill({ json: { countries: [], regions: [], movements: [], topics: [], kinds: [] } }));
  await page.route("**/api/backend/v1/painters/options?*", route => route.fulfill({ json: { items: [], selected: [], has_more: false } }));
  await page.route(`**/api/backend/v1/${endpoint}?*`, route => {
    const params = new URL(route.request().url()).searchParams;
    requests.push(params);
    const filtered = params.has(example.key);
    const requestedRange = { start: Number(params.get("start")), end: Number(params.get("end")) };
    const periods = filtered ? [] : [{ start_year: range.start, end_year: range.end, count: 500 }];
    const common = {
      range: requestedRange, total: filtered ? 1 : 500,
      mode: filtered ? "individual" as const : "density" as const,
      // Matching lifespans/events can extend beyond the selected years.
      matchedRange: filtered ? { start: 1880, end: 1950 } : range,
      suggested_filters: filtered ? [] : [{ key: example.key, value: example.value, name: example.value === "FR" ? "France" : example.value, count: 1 }],
    };
    const response = events ? {
      ...common, bounds: { start: -12000, end: 2000 }, selectionTotal: 500,
      undatedTotal: 0, hasMore: false, nextCursor: "", ticks: [], density: periods,
      items: filtered ? [{
        id: "sample-event", title: "Sample event", startYear: 1880, endYear: 1950, years: "1880–1950", approximate: false, kind: "Period",
        sourceId: "sample", sourceRevision: 1, sourceUrl: "", description: "", significance: "", dateBasis: "Browser fixture",
        topics: [], countries: [], regions: [], geographyBasis: "", locations: [], people: [], sources: [], connections: [],
        top100: false, selectionBasis: "Browser fixture", status: "review",
      }] : [],
    } as EventsResponse : {
      ...common, popular_only: false, bins: [], periods,
      items: filtered ? [{ id: "sample-painter", slug: "sample-painter", name: "Sample painter", start_year: 1880, end_year: 1950, date_display: "1880–1950", movement: { slug: "impressionism", name: "Impressionism", color: "#abcdef" }, countries: ["FR"], artwork_count: 1, status: "review" }] : [],
    } as TimelineResponse;
    return route.fulfill({ json: response });
  });

  const params = new URLSearchParams({ start: String(range.start), end: String(range.end), q: "sample", region: "europe", [events ? "top100" : "popular"]: "false" });
  if (events) params.set("after", "previous-page");
  else params.set("women", "true");
  await page.goto(`${events ? "/events" : "/"}?${params}`);
  await settled(page, 500, example.view);
  const before = page.url();
  const selector = example.action === "button" ? ".density-actions" : example.action === "column" ? ".period-chart" : ".density-results";
  await page.locator(selector).getByRole("button").first().click();
  await settled(page, 1, events ? "events" : "painter");

  async function expectSelection() {
    const current = new URL(page.url()).searchParams;
    for (const [key, value] of params) if (key !== "after") expect(current.get(key), key).toBe(value);
    expect(current.get(example.key)).toBe(example.value);
    expect(current.has("fit")).toBe(false);
    expect(current.has("after")).toBe(false);
    await expect(page.locator(".year-inputs input").first()).toHaveValue(String(range.start));
    await expect(page.locator(".year-inputs input").last()).toHaveValue(String(range.end));
  }
  await expectSelection();
  for (const request of requests) {
    expect(request.get("start")).toBe(String(range.start));
    expect(request.get("end")).toBe(String(range.end));
  }
  await page.reload();
  await settled(page, 1, events ? "events" : "painter");
  await expectSelection();
  await page.goBack();
  await expect(page).toHaveURL(before);
  await settled(page, 500, example.view);
  await page.goForward();
  await settled(page, 1, events ? "events" : "painter");
  await expectSelection();
});
