import { expect, test } from "@playwright/test";
import type { AtlasResponse } from "../lib/atlas";

for (const [id, title, years] of [
  ["wd-q119224", "Norna-Gests þáttr", "c. 1300"],
  ["wd-q180736", "Les Misérables", "1862"],
  ["wd-q188538", "The Master and Margarita", "1966–1967"],
  ["wd-q83799", "We", "1924"],
]) test(`${title} shows reviewed dates and a dating source`, async ({ page }) => {
  await page.goto(`/books?book=${id}`);
  const drawer = page.getByRole("dialog", { name: "Book details", exact: true });
  await expect(drawer.getByRole("heading", { level: 2 })).toHaveText(title);
  await expect(drawer.locator("header > p").last()).toHaveText(years);
  const source = drawer.getByRole("link", { name: /^Dating source:/ }).first();
  await expect(source).toHaveAttribute("href", /^https:\/\//);
  await expect(drawer).not.toContainText("1301–2000");
});

for (const preset of ["russian-revolution", "french-revolution"]) test(`${preset} keeps its subject focus through dates, layer switches and reload`, async ({ page }) => {
  const expected = await (await page.request.get(`/api/backend/v1/atlas?preset=${preset}`)).json() as AtlasResponse;
  const events = expected.lanes.find(lane => lane.key === "event")!;
  expect(events.items.filter(item => item.relation === "context")).toHaveLength(3);
  await page.goto(`/all?preset=${preset}`);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.locator(".all-canvas-heading [role=status]")).toHaveText(`${expected.total.toLocaleString("en-GB")} entries`);
  await page.getByRole("button", { name: "Events", exact: true }).click();
  const browse = page.getByRole("dialog", { name: "Browse events", exact: true });
  await expect(browse.locator("li")).toHaveCount(events.total);
  await expect(browse.getByText(/^Context ·/)).toHaveCount(3);
  await page.keyboard.press("Escape");
  await page.getByLabel("All start year", { exact: true }).fill(preset === "russian-revolution" ? "1910" : "1780");
  await page.getByLabel("All start year", { exact: true }).press("Enter");
  await expect(page).toHaveURL(new RegExp(`preset=${preset}`));
  await page.getByRole('checkbox', { name: 'Books', exact: true }).uncheck();
  await expect(page.locator('#all-lane-book')).toHaveCount(0);
  await page.getByRole('checkbox', { name: 'Books', exact: true }).check();
  await page.reload();
  await expect(page).toHaveURL(new RegExp(`preset=${preset}`));
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
  await expect(page.getByRole("checkbox", { name: "Highlights", exact: true })).not.toBeChecked();
  await page.getByRole("checkbox", { name: "Highlights", exact: true }).check();
  await page.getByRole("checkbox", { name: "Highlights", exact: true }).uncheck();
  await expect(page).toHaveURL(/highlights=false/);
  await expect(page).not.toHaveURL(/book_top100=true/);
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy", "false");
});

test("French Revolution artwork opens with its sourced image and original date", async ({ page }) => {
  await page.goto("/all?preset=french-revolution&itemType=artwork&item=bd026785-c3e7-5370-a47d-5731a5406a61");
  const drawer = page.getByRole("dialog", { name: "Artwork details", exact: true });
  await expect(drawer.getByRole("heading", { level: 2 })).toContainText("Marat");
  await expect(drawer.locator("header > p").last()).toHaveText("1793");
  await drawer.getByRole("button", { name: /View larger/ }).click();
  const large = page.getByRole("dialog", { name: /Enlarged image:/ });
  await expect(large.locator("img")).toHaveJSProperty("complete", true);
  expect(await large.locator("img").evaluate((node: HTMLImageElement) => node.naturalWidth)).toBeGreaterThan(0);
  await expect(large.getByRole("button", { name: "Next artwork", exact: true })).toBeEnabled();
});
