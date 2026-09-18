import {expect,test,type Page} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
async function ready(page:Page){await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy','false',{timeout:20000});await expect(page.getByRole('heading',{name:'We couldn’t load this view'})).toHaveCount(0)}
async function start(page:Page){await page.goto('/all');await page.getByRole('button',{name:'The First World War',exact:true}).click();await ready(page)}
for(const width of [1440,390,320])test(`empty canvas, navigation and accessibility at ${width}`,async({page},info)=>{
 await page.setViewportSize({width,height:900});const requests:string[]=[];page.on('request',r=>{if(r.url().includes('/api/backend/v1/atlas?'))requests.push(r.url())});await page.goto('/all');
 await expect(page.getByRole('button',{name:'The First World War',exact:true})).toBeVisible();expect(requests).toEqual([]);
 await expect(page.getByRole('navigation',{name:'Primary navigation'}).getByRole('link')).toHaveText(['Painters','Books','Events','All']);
 await expect(page.locator('.all-lane')).toHaveCount(0);await expect(page.getByRole('heading',{name:'Explore the entries'})).toHaveCount(0);await expect(page.getByRole('button',{name:'Add to atlas',exact:true})).toHaveCount(0);await expect(page.locator('.site-footer')).toBeHidden();
 await expect(page.getByLabel('Historical period',{exact:true}).locator('optgroup option')).toHaveCount(30);
 expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBeLessThanOrEqual(900);expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);await page.screenshot({path:info.outputPath(`empty-${width}.png`)});
});
for(const width of [1440,390,320])test(`populated canvas fits the screen at ${width}`,async({page},info)=>{
 await page.setViewportSize({width,height:900});await start(page);await expect(page.locator('.all-lane')).toHaveCount(3);await expect(page.locator('.tick-row')).toBeVisible();
 await expect(page.locator('main')).not.toContainText('Compare the years before the war');await expect(page.locator('main')).not.toContainText('About this lens');
 expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBeLessThanOrEqual(900);expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
 const controls=await page.getByLabel('All end year',{exact:true}).boundingBox();expect(controls!.y+controls!.height).toBeLessThan(900);
 expect((await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);await page.screenshot({path:info.outputPath(`wwi-${width}.png`)});
});
test('period descriptions and main window remain in a details panel; clear returns to empty',async({page})=>{
 await start(page);await page.getByRole('button',{name:'About this period',exact:true}).click();const panel=page.getByRole('dialog',{name:'Historical period details'});await expect(panel).toContainText('Compare the years before the war');await panel.getByLabel('Time window',{exact:true}).selectOption('period');await panel.getByRole('button',{name:'Close period details',exact:true}).click();await ready(page);await expect(page.getByLabel('All start year',{exact:true})).toHaveValue('1914');await expect(page.getByLabel('All end year',{exact:true})).toHaveValue('1918');await page.getByRole('button',{name:'Clear',exact:true}).click();await expect(page.getByRole('heading',{name:'Choose a starting point'})).toBeVisible();await expect(page.locator('.all-lane')).toHaveCount(0);
});
for(const kind of ['Artworks','Books','Events'])test(`Add enables existing ${kind} layer without writes`,async({page})=>{
 const writes:string[]=[];page.on('request',r=>{if(r.url().includes('/api/')&&r.method()!=='GET')writes.push(r.url())});await page.goto('/all');await page.getByRole('button',{name:'+ Add',exact:true}).click();const picker=page.getByRole('dialog',{name:'Add a layer'});await picker.getByRole('button',{name:kind,exact:true}).click();await expect(picker.getByLabel('Source link')).toHaveCount(0);await expect(picker.getByLabel('Editor token')).toHaveCount(0);
 await expect(picker.locator('.atlas-picker-list,.atlas-picker-pages')).toHaveCount(0);await picker.getByRole('button',{name:`Add ${kind.toLowerCase()} layer`,exact:true}).click();await ready(page);await expect(page.locator('.all-lane')).toHaveCount(1);await expect(page.locator('.all-lane>header h2')).toHaveText(kind);expect(writes).toEqual([]);await page.reload();await ready(page);await expect(page.locator('.all-lane>header h2')).toHaveText(kind);await page.getByRole('button',{name:`Remove ${kind.toLowerCase()} from timeline`}).click();await expect(page.getByRole('heading',{name:'Choose a starting point'})).toBeVisible();
});
test('Add saves a searched book layer and keeps native details available',async({page})=>{
 await page.goto('/all');await page.getByRole('button',{name:'+ Add',exact:true}).click();const picker=page.getByRole('dialog',{name:'Add a layer'});await picker.getByRole('button',{name:'Books',exact:true}).click();await picker.getByLabel('Find a book or author',{exact:true}).fill('Metamorphosis');
 await expect(picker.getByText('1 matching entries',{exact:true})).toBeVisible();await expect(picker.locator('.atlas-picker-list')).toHaveCount(0);await expect(picker).not.toContainText('choose individual');await picker.getByRole('button',{name:'Add books layer',exact:true}).click();await ready(page);await expect(page).toHaveURL(/type=book/);await expect(page).toHaveURL(/book_q=Metamorphosis/);await expect(page).not.toHaveURL(/pick_/);
 await page.reload();await ready(page);await expect(page.locator('.timeline-mark')).toHaveCount(1);await page.locator('.timeline-mark').click();await expect(page.getByRole('dialog')).toContainText('The Metamorphosis');await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});
test('whole artwork and event layers coexist without individual selection controls',async({page})=>{
 await page.goto('/all');for(const kind of ['Artworks','Events']){await page.getByRole('button',{name:'+ Add',exact:true}).click();const picker=page.getByRole('dialog',{name:'Add a layer'});await picker.getByRole('button',{name:kind,exact:true}).click();await expect(picker.getByRole('button',{name:`Add ${kind.toLowerCase()} layer`,exact:true})).toBeEnabled();await expect(picker.locator('.atlas-picker-list')).toHaveCount(0);await expect(picker.getByRole('button',{name:'Next page',exact:true})).toHaveCount(0);await picker.getByRole('button',{name:`Add ${kind.toLowerCase()} layer`,exact:true}).click();await ready(page)}
 await expect(page.locator('.all-lane>header h2')).toHaveText(['Artworks','Events']);await expect(page).not.toHaveURL(/pick_/);await page.reload();await ready(page);await expect(page.locator('.all-lane>header h2')).toHaveText(['Artworks','Events']);
});
test('legacy individual selections do not populate All or leak into layer requests',async({page})=>{
 const requests:string[]=[];page.on('request',r=>{if(r.url().includes('/api/backend/v1/atlas?'))requests.push(r.url())});await page.goto('/all?selection=true&pick_book=old-book');await expect(page.getByRole('heading',{name:'Choose a starting point'})).toBeVisible();expect(requests).toEqual([]);await page.getByRole('button',{name:'The First World War',exact:true}).click();await ready(page);await expect(page).not.toHaveURL(/pick_/);expect(requests.every(url=>!url.includes('pick_'))).toBe(true);
});
for(const kind of ['artworks','books','events'])test(`Browse ${kind} opens bounded entries in a side panel`,async({page})=>{
 await start(page);await page.getByRole('button',{name:`Browse ${kind}`,exact:true}).click();const panel=page.getByRole('dialog',{name:`Browse ${kind}`,exact:true});await expect(panel.locator('.atlas-picker-list li').first()).toBeVisible();expect(await panel.locator('.atlas-picker-list li').count()).toBeLessThanOrEqual(30);
 if(kind==='artworks'){const first=await panel.locator('li strong').first().textContent();await panel.getByRole('button',{name:'Next page',exact:true}).click();await expect(panel.locator('li strong').first()).not.toHaveText(first!)}
 await panel.getByRole('button',{name:/^Read /}).first().click();await expect(page.getByRole('dialog')).toHaveCount(1);await expect(page.getByRole('dialog').getByRole('heading').first()).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);await expect(page.getByRole('button',{name:`Browse ${kind}`,exact:true})).toBeFocused();
});
test('year edits, BCE validation, density drill-down and history',async({page})=>{
 await start(page);await page.locator('.all-lane').first().getByRole('button',{name:/^Explore /}).first().click();await ready(page);expect(Number(await page.getByLabel('All end year',{exact:true}).inputValue())-Number(await page.getByLabel('All start year',{exact:true}).inputValue())).toBeLessThan(20);
 await page.getByLabel('All start year',{exact:true}).fill('-500');await page.getByLabel('All end year',{exact:true}).fill('500');await page.getByLabel('All end year',{exact:true}).press('Enter');await ready(page);await expect(page.locator('h1')).toContainText('500 BCE');await page.reload();await ready(page);await expect(page.getByLabel('All start year',{exact:true})).toHaveValue('-500');await page.getByLabel('All start year',{exact:true}).fill('0');await page.getByLabel('All start year',{exact:true}).press('Enter');await expect(page.locator('.year-error')).toContainText('no year zero');await page.getByLabel('All start year',{exact:true}).press('Escape');await page.goBack();await ready(page);await expect(page.getByLabel('All start year',{exact:true})).not.toHaveValue('-500');
});
test('shared filter bar retains region, query and highlights and removes chips',async({page})=>{
 await start(page);
 const filters=page.locator('.all-explorer > .atlas-filter-system');
 await expect(filters.getByLabel('Region',{exact:true})).toBeVisible();
 await filters.getByLabel('Region',{exact:true}).selectOption('eastern-europe');
 await filters.getByRole('checkbox',{name:'Highlights',exact:true}).uncheck();
 await filters.getByLabel('Search the timeline',{exact:true}).fill('Revolution');
 await ready(page);await page.reload();await ready(page);
 await expect(filters.getByLabel('Region',{exact:true})).toHaveValue('eastern-europe');
 await expect(filters.getByLabel('Search the timeline',{exact:true})).toHaveValue('Revolution');
 await page.getByRole('button',{name:'Remove Eastern Europe filter',exact:true}).click();
 await ready(page);await expect(filters.getByLabel('Region',{exact:true})).toHaveValue('');
 await expect(filters.getByLabel('Search the timeline',{exact:true})).toBeFocused();
 await expect(page.getByLabel('All start year',{exact:true})).toHaveValue('1910');
 await page.getByRole('button',{name:'Clear filters',exact:true}).click();
 await ready(page);await expect(filters.getByLabel('Search the timeline',{exact:true})).toHaveValue('');
 await expect(filters.getByRole('checkbox',{name:'Highlights',exact:true})).not.toBeChecked();
 await expect(page.locator('.all-lane')).toHaveCount(3);
 await filters.getByRole('button',{name:'Reset view',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Choose a starting point'})).toBeVisible();
 await expect(filters.getByRole('checkbox',{name:'Highlights',exact:true})).toBeChecked();
});
test('retired draft intake cannot create content',async({request})=>{expect((await request.post('/api/backend/v1/atlas/drafts',{data:{title:'Must not be stored'}})).status()).toBe(404)});
