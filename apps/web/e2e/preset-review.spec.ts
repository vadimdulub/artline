import { expect, test } from "@playwright/test";
import type { AtlasMetadata, AtlasResponse } from "../lib/atlas";

const presets = ["writing", "classical", "buddhism", "silk-roads", "byzantium", "islamic-learning", "tang-song", "sahel", "mongol", "renaissance", "reformation", "atlantic", "mughal", "edo", "science", "enlightenment", "french-revolution", "industrial", "romanticism", "empire", "modernism", "first-world-war", "russian-revolution", "interwar", "second-world-war", "decolonization", "cold-war", "civil-rights", "space-age", "digital"];

for (const id of presets) test(`${id}: reviewed focus, sources, context labels and main-period window`, async ({ page }) => {
  const metadata = await (await page.request.get("/api/backend/v1/atlas/presets")).json() as AtlasMetadata;
  const preset = metadata.presets.find(preset => preset.id === id)!;
  expect(preset.focus?.label).toBeTruthy();
  const response = await page.request.get(`/api/backend/v1/atlas?preset=${id}`);
  expect(response.ok()).toBeTruthy();
  const data = await response.json() as AtlasResponse;
  expect(data.lanes).toHaveLength(3);
  expect(data.lanes.every(lane => lane.items.length <= 150)).toBe(true);
  await page.goto(`/all?preset=${id}`);
  const stage = page.locator(".timeline-stage");
  await expect(stage).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".all-explorer").getByRole("alert")).toHaveCount(0);
  await expect(page.locator(".all-canvas-heading [role=status]")).toHaveText(`${data.total.toLocaleString("en-GB")} entries`);
  await expect(page.getByRole("checkbox", { name: "Highlights", exact: true })).toBeChecked({ checked: preset.startingHighlights });
  const contexts = data.lanes.find(lane => lane.key === "event")!.items.filter(item => item.relation === "context");
  await page.getByRole("button", { name: "Events", exact: true }).click();
  const browse = page.getByRole("dialog", { name: "Browse events", exact: true });
  await expect(browse.getByText(/^Context ·/)).toHaveCount(contexts.length);
  await page.keyboard.press("Escape");
  const details = page.locator('.all-view-context');
  await details.locator('summary').click();
  await expect(details).toContainText(preset.description);
  expect(preset.sources.length).toBeGreaterThan(0);
  expect(preset.sources.every(source => source.url.startsWith('https://'))).toBe(true);
  await page.goto(`/all?preset=${id}&window=period`);
  await expect(stage).toHaveAttribute("aria-busy", "false");
  await expect(page.getByLabel("All start year", { exact: true })).toHaveValue(String(preset.period.start));
  await expect(page.getByLabel("All end year", { exact: true })).toHaveValue(String(preset.period.end));
  await expect(page).toHaveURL(new RegExp(`preset=${id}`));
});

for (const [preset, kind, id] of [
  ["renaissance", "event", "event-q4692"],
  ["science", "book", "wd-q1768303"],
  ["mongol", "book", "wd-q469930"],
  ["digital", "event", "event-q75"],
]) test(`${preset}: core ${kind} survives the native Highlights filter`, async ({ request }) => {
  const response = await request.get(`/api/backend/v1/atlas?preset=${preset}&type=${kind}&highlights=true&${kind}_top100=true`);
  expect(response.ok()).toBeTruthy();
  const data = await response.json() as AtlasResponse;
  expect(data.lanes[0].items.map(item => item.id)).toContain(id);
  const other = data.lanes[0].items.find(item => item.id !== id)!;
  const mixedResponse = await request.get(`/api/backend/v1/atlas?preset=${preset}&selection=true&type=${kind}&highlights=true&pick_${kind}=${other.id}`);
  expect(mixedResponse.ok()).toBeTruthy();
  const mixed = await mixedResponse.json() as AtlasResponse;
  expect(mixed.lanes[0].items.map(item => item.id)).toContain(id);
  expect(mixed.total).toBe(data.total);
  const filtered = await (await request.get(`/api/backend/v1/atlas?preset=${preset}&type=${kind}&highlights=true&country=not-a-recorded-country`)).json() as AtlasResponse;
  expect(filtered.total).toBe(0);
});

test("Space Age: mobile browsing keeps selected missions and labelled context", async ({ page }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/all?preset=space-age");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await page.getByRole("button", { name: "Events", exact: true }).click();
  const browse = page.getByRole("dialog", { name: "Browse events", exact: true });
  await expect(browse).toContainText("Apollo 11");
  await expect(browse).not.toContainText(/Apollo (18|19|20)\b/);
  await expect(browse.getByText(/^Context ·/)).toHaveCount(3);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: info.outputPath("space-age-context-mobile.png") });
});

test("Byzantium retains recorded anonymous works through its object tradition", async ({ request }) => {
  const response = await request.get("/api/backend/v1/atlas?preset=byzantium&type=artwork&highlights=true&q=Martyrdom%20of%20St.%20Lawrence");
  expect(response.ok()).toBeTruthy();
  const data = await response.json() as AtlasResponse;
  expect(data.lanes[0].items).toEqual(expect.arrayContaining([expect.objectContaining({
    id: "97e12cc8-1ba8-548a-9677-a03813b0acec", context: "Creator not recorded", startYear: 425,
  })]));
});
