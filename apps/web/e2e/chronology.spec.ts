import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { ArtistDetail, ArtistWorksPage, Artwork } from "../lib/types";

async function fixture(page: Page, count: number) {
  const artist = await (await page.request.get("/api/backend/v1/artists/giotto")).json() as ArtistDetail;
  const items = Array.from({ length: count }, (_, index): Artwork => ({ ...artist.artworks[0], id: `00000000-0000-0000-0000-${String(index).padStart(12, "0")}`, title: `Chronology fixture ${index+1}`, slug: `chronology-fixture-${index}`, date_precision: index===count-1 ? "unknown" : index===0 ? "circa_range" : "exact", date_display: index===count-1 ? "Creation date unknown" : index===0 ? "c. 1300–1302" : "1320", creation_year_start: index===count-1 ? null : index===0 ? 1300 : 1320, creation_year_end: index===count-1 ? null : index===0 ? 1302 : 1320, representative_order: null }));
  const years = count ? [{ year: 1300, count: 1 }, { year: 1320, count: count-2 }] : [];
  await page.route(/\/api\/backend\/v1\/artists\/giotto\/works(?:\?|$)/, async route => {
    const query = new URL(route.request().url()).searchParams;
    const selected = query.get("undated") === "1" ? items.filter(item => item.date_precision==="unknown") : query.get("year") ? items.filter(item => String(item.creation_year_start)===query.get("year")) : items;
    const offset = query.get("cursor") ? 24 : 0, visible = selected.slice(offset,offset+24);
    const groups: ArtistWorksPage["groups"] = [];
    visible.forEach((work,index) => { const year=work.creation_year_start; let group=groups.at(-1); if (!group || group.year!==year) {group={ year, start_index: index,count:0,has_uncertain_dates:false };groups.push(group)} group.count++;group.has_uncertain_dates ||= work.date_precision!=="exact"; });
    const response: ArtistWorksPage = {items:visible,years,total:count,undated_count:count ? 1 : 0,matching_total:selected.length,next_cursor: offset+24 < selected.length ? "fixture-next" : "",range_start:artist.timeline_start_year,range_end:artist.timeline_end_year,groups};
    await route.fulfill({ json: response });
  });
}

test("painter clicks show a dated chronology and keep source ranges intact", async ({ page }) => {
  await fixture(page,40);
  await page.goto("/?q=Giotto");
  await page.locator(".artist-mark").filter({hasText:"Giotto di Bondone"}).click();
  const panel = page.getByRole("dialog", { name: "Painter details", exact:true });
  await expect(panel.getByRole("heading", { name:"Artworks by year",exact:true })).toBeVisible();
  await expect(panel.getByRole("combobox", { name:"Artwork year",exact:true })).toHaveValue("");
  await expect(panel.getByRole("region", { name:"Artworks grouped at 1300",exact:true }).locator(".work-row")).toHaveCount(1);
  await expect(panel.locator(".work-row .work-date").first()).toHaveText("c. 1300–1302");
  await panel.getByRole("combobox", { name:"Artwork year",exact:true }).selectOption("1300");
  await page.reload();
  await expect(panel.getByRole("combobox", { name:"Artwork year",exact:true })).toHaveValue("1300");
  await page.goto("/?artist=giotto");
  await panel.getByRole("button", { name:"Next painter",exact:true }).click();
  await expect(panel.getByRole("combobox", { name:"Artwork year",exact:true })).toHaveValue("");
});

test("a larger catalogue pages on the server and places undated records at the end", async ({ page }) => {
  await fixture(page,40);
  await page.goto("/?artist=giotto");
  const panel=page.getByRole("dialog", { name:"Painter details",exact:true });
  await expect(panel.locator(".work-row")).toHaveCount(24);
  await expect(panel.getByRole("region",{name:"Artworks by year",exact:true}).getByRole("status")).toHaveText("40 recorded works");
  await expect(panel.locator(".work-row .work-title").first()).toHaveText("Chronology fixture 1");
  await panel.getByRole("button", { name:"Next artworks",exact:true }).click();
  await expect(panel.locator(".work-row")).toHaveCount(16);
  await expect(panel.locator(".work-row .work-title").last()).toHaveText("Chronology fixture 40");
  await panel.getByRole("button", { name:"Previous artworks",exact:true }).click();
  await expect(panel.locator(".work-row")).toHaveCount(24);
  await expect(panel.locator(".work-row .work-title").first()).toHaveText("Chronology fixture 1");
  await panel.getByRole("button", { name:"Next artworks",exact:true }).click();
  await expect(panel.locator(".work-row")).toHaveCount(16);
  await expect(panel.getByRole("region", { name:"Undated artworks",exact:true })).toBeVisible();
  const marker=panel.getByRole("button", { name:/1 undated.*missing-data/ });
  await marker.click();
  await expect(panel.getByText(/1 artwork has no recorded creation year/).first()).toBeVisible();
  await expect(panel.locator(".work-row")).toHaveCount(1);
  await expect(panel.locator(".work-row .work-date")).toHaveText("Creation date unknown");
  await expect(panel.getByRole("combobox", { name:"Artwork year",exact:true })).toHaveValue("undated");
});

test("missing data is explicit at the interval's end, including on phones", async ({ page }) => {
  await fixture(page,0);
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width,height:900});
    await page.goto("/?artist=giotto");
    const panel=page.getByRole("dialog", { name:"Painter details",exact:true });
    const marker=panel.getByRole("button", {name:/No data.*missing-data/});
    await expect(marker).toBeVisible();
    await marker.focus();
    await expect(marker).toBeFocused();
    await expect(panel.getByText(/We don’t have artwork data for this painter yet/)).toBeVisible();
    await expect(panel.locator(".work-row")).toHaveCount(0);
    const chart=panel.getByRole("img",{name:/Recorded artwork dates across/});
    expect((await marker.boundingBox())!.x).toBeGreaterThan((await chart.boundingBox())!.x+(await chart.boundingBox())!.width);
    expect(await panel.evaluate(node=>node.scrollWidth)).toBeLessThanOrEqual((await panel.boundingBox())!.width);
    const scan=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({path:`../../docs/screenshots/chronology-empty-${width}.png`});
  }
});

test("chronology failures are not presented as missing data and recover", async ({ page }) => {
  await page.route(/\/api\/backend\/v1\/artists\/giotto\/works(?:\?|$)/,route=>route.fulfill({status:503,json:{error:{message:"Connection test failure"}}}));
  await page.goto("/?artist=giotto");
  const panel=page.getByRole("dialog",{name:"Painter details",exact:true});
  await expect(panel.getByRole("alert")).toContainText("Connection test failure");
  await expect(panel.getByRole("button",{name:/No data.*missing-data/})).toHaveCount(0);
  await page.unroute(/\/api\/backend\/v1\/artists\/giotto\/works(?:\?|$)/);
  await fixture(page,40);
  await panel.getByRole("button",{name:"Retry chronology",exact:true}).click();
  await expect(panel.locator(".work-row")).toHaveCount(24);
  await page.screenshot({path:"../../docs/screenshots/chronology-desktop.png"});
  await page.setViewportSize({width:390,height:844});
  await panel.getByRole("heading",{name:"Artworks by year",exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:"../../docs/screenshots/chronology-mobile.png"});
});
