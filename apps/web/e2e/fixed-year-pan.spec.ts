import { expect, test } from "@playwright/test";

// Real headless Chrome and real, read-only catalogue responses.
for (const [route, start, end] of [["/books",1500,1800],["/",1300,1600],["/events",1500,1800]] as const) {
  test(`${route} previews a fixed-width range and updates the chart on release`, async ({page}) => {
    await page.goto(`${route}${route.includes("?")?"&":"?"}start=${start}&end=${end}`);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
    const tickPositions=()=>page.locator(".tick-row > span").evaluateAll(nodes=>nodes.map(node=>({label:node.textContent,left:(node as HTMLElement).style.left})));
    const initialTicks=await tickPositions();
    const band=page.getByRole("button",{name:"Move selected time range",exact:true});
    await band.scrollIntoViewIfNeeded();
    const before=(await band.boundingBox())!, track=(await page.locator(".range-track").boundingBox())!;
    const url=page.url(), x=before.x+before.width/2, y=track.y+track.height/2;
    await page.mouse.move(x,y); await page.mouse.down();
    for(const delta of [.04,.08,.12]) {
      await page.mouse.move(x+track.width*delta,y,{steps:5});
      expect(page.url()).toBe(url);
      expect(await tickPositions()).toEqual(initialTicks);
      const moved=(await band.boundingBox())!;
      expect(Math.abs(moved.width-before.width)).toBeLessThan(1);
      expect(Math.abs(moved.x-before.x-track.width*delta)).toBeLessThan(1);
    }
    await page.mouse.up();
    await expect.poll(()=>page.url()).not.toBe(url);
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
    expect(Math.abs((await band.boundingBox())!.width-before.width)).toBeLessThan(track.width*.003);
    const fields=page.locator(".year-inputs input");
    const ticks = await tickPositions();
    expect(ticks[0]).toEqual({ label: await fields.first().inputValue(), left: "0%" });
    expect(ticks.at(-1)).toEqual({ label: await fields.last().inputValue(), left: "100%" });
    await expect(page.locator(".timeline-selected-years")).toHaveCount(0);
    expect(Number(await fields.first().inputValue())).toBeGreaterThan(start);
    await band.focus(); await band.press("ArrowLeft");
    await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
    expect(Math.abs((await band.boundingBox())!.width-before.width)).toBeLessThan(track.width*.004);
  });
}

test("Books ends at 2000 and has no Collections filter, including in Add",async({page})=>{
  const response=await page.request.get("/api/backend/v1/books?limit=1");
  expect(response.ok()).toBe(true);
  const books=await response.json();expect(books.bounds.end).toBe(2000);expect(books).not.toHaveProperty("collections");
  expect((await page.request.get("/api/backend/v1/books?end=2001")).status()).toBe(400);
  await page.goto("/books?collection=Modern");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
  await expect(page.getByLabel("Book end year")).toHaveValue("2000");
  await expect(page.locator('summary[aria-label^="Collections:"]')).toHaveCount(0);
  await page.goto("/all?panel=add");
  const dialog=page.getByRole("dialog",{name:"Add a layer"});
  await dialog.getByRole("button",{name:"Books",exact:true}).click();
  await expect(dialog.locator('summary[aria-label^="Collections:"]')).toHaveCount(0);
  await expect(dialog.locator('summary[aria-label^="Languages:"]')).toBeVisible();
});

test("All countries and continents persist and constrain Add counts",async({page},info)=>{
  await page.goto("/all?type=book&type=event&type=artwork&selection=true&start=1800&end=1950");
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
  const dialog=page.locator(".all-explorer > .atlas-filter-system");
  await dialog.locator('summary[aria-label^="Continents:"]').click();
  await dialog.getByRole("checkbox",{name:"Europe",exact:true}).check();
  await dialog.locator('summary[aria-label^="Countries:"]').click();
  await dialog.getByLabel("Search countries",{exact:true}).fill("France");
  await dialog.getByRole("checkbox",{name:"France",exact:true}).check();
  await page.screenshot({path:info.outputPath("all-geography-desktop.png")});
  await dialog.getByRole("button",{name:"Done",exact:true}).first().click();
  await expect(page).toHaveURL(/continent=europe/);await expect(page).toHaveURL(/country=france/);
  await page.reload();
  await expect(page.locator(".timeline-stage")).toHaveAttribute("aria-busy","false");
  await page.getByRole("button",{name:"+ Add",exact:true}).click();
  const add=page.getByRole("dialog",{name:"Add a layer"});
  await add.getByRole("button",{name:"Books",exact:true}).click();
  const expected=await (await page.request.get("/api/backend/v1/atlas?selection=false&type=book&start=1800&end=1950&continent=europe&country=france&highlights=true&book_top100=true&limit=1")).json();
  await expect(add.locator(".atlas-layer-action [role=status]")).toHaveText(`${expected.total.toLocaleString("en-GB")} matching entries`);
  await add.getByRole("button",{name:"Update books layer",exact:true}).click();
  await expect(page).toHaveURL(/country=france/);
  await page.setViewportSize({width:390,height:844});
  await dialog.getByRole("button",{name:"Filters",exact:true}).click();
  await dialog.locator('summary[aria-label^="Countries:"]').click();
  await expect(dialog.getByRole("checkbox",{name:"France",exact:true})).toBeChecked();
  await page.screenshot({path:info.outputPath("all-geography-mobile.png")});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await dialog.getByRole("button",{name:"Done",exact:true}).click();
  await page.getByRole("button",{name:"Clear filters",exact:true}).click();
  expect(new URL(page.url()).searchParams.has("country")).toBe(false);
  expect(new URL(page.url()).searchParams.has("continent")).toBe(false);
});
