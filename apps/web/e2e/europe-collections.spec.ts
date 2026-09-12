import {test,expect} from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("European shortcut preserves multiple painters and index pages are reversible", async ({page}) => {
  await page.goto("/museums?artist=claude-monet&artist=camille-pissarro-q134741");
  await page.getByRole("button",{name:"European museums",exact:true}).click();
  const params=new URL(page.url()).searchParams;
  expect(params.getAll("region").sort()).toEqual(["eastern-europe","northern-europe","southern-europe","western-europe"]);
  expect(params.getAll("artist")).toHaveLength(2);
  const response=await page.request.get(`/api/backend/v1/museums?${params}`);
  expect(response.ok()).toBe(true);
  const data=await response.json();
  expect(data.total).toBeGreaterThan(0);
  expect(data.items.every((museum:{venues:{region:string}[]})=>museum.venues.some(venue=>params.getAll("region").includes(venue.region)))).toBe(true);
  await expect(page.getByRole("button",{name:"European museums",exact:true})).toHaveAttribute("aria-pressed","true");
  await page.goto("/museums");
  const results=page.getByRole("region",{name:"Museum results"});
  await expect(results.getByRole("link").first()).toBeVisible();
  const first=await results.getByRole("link").first().getAttribute("href");
  const pages=page.getByRole("navigation",{name:"Museum pages"});
  await pages.getByRole("button",{name:"Next page",exact:true}).click();
  await expect(results.getByRole("link").first()).not.toHaveAttribute("href",first!);
  await pages.getByRole("button",{name:"Previous page",exact:true}).click();
  await expect(results.getByRole("link").first()).toHaveAttribute("href",first!);
});

test("European images are local, under 100 KB, and usable in the drawer", async ({page}) => {
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width,height:1000});
    await page.goto("/museums/statens-museum-for-kunst?image_only=1");
    const results=page.getByRole("region",{name:"Museum artwork results"});
    await expect(results.getByRole("button")).toHaveCount(24);
    const img=results.locator('img[src*="smk-"]').first();
    await expect(img).toBeVisible();
    await expect.poll(()=>img.evaluate((node:HTMLImageElement)=>node.complete&&node.naturalWidth>0)).toBe(true);
    const rendered=await img.getAttribute("src");
    const src=new URL(rendered!,page.url()).searchParams.get("url") ?? rendered;
    expect(src).toMatch(/^\/assets\/artworks\/imported\/smk-[a-f0-9]{64}\.jpg$/);
    const image=await page.request.get(src!);
    expect(image.ok()).toBe(true);expect((await image.body()).length).toBeLessThanOrEqual(100000);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    if(width<1000) await results.scrollIntoViewIfNeeded();
    await page.screenshot({path:`../../docs/screenshots/europe-smk-grid-${width}.png`});
    await img.locator("xpath=ancestor::button").click();
    const panel=page.getByRole("dialog",{name:"Museum artwork details",exact:true});
    await expect(panel.getByRole("button",{name:/View larger/})).toBeVisible();
    await expect(panel.getByText("Public Domain Mark 1.0",{exact:false}).first()).toBeVisible();
    expect(await panel.evaluate(node=>node.scrollWidth)).toBeLessThanOrEqual(width);
    const scan=await new AxeBuilder({page}).withTags(["wcag2a","wcag2aa","wcag21aa","wcag22aa"]).analyze();
    expect(scan.violations).toEqual([]);
    await page.screenshot({path:`../../docs/screenshots/europe-smk-drawer-${width}.png`});
    await page.keyboard.press("Escape");
    await expect(img.locator("xpath=ancestor::button")).toBeFocused();
  }
});
