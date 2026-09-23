import { expect, test, type Page, type Locator } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { AtlasResponse } from '../lib/atlas';

async function ready(page: Page) {
  await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('.all-explorer').getByRole('alert')).toHaveCount(0);
}
async function choose(page: Page, label: string, names: string[]) {
  const filters = page.locator('.all-explorer > .atlas-filter-system');
  const summary = filters.locator('summary').filter({ hasText: label });
  if (!await summary.isVisible()) await filters.getByRole('button', { name: 'Filters', exact: true }).click();
  const picker = summary.locator('..');
  await summary.click();
  for (const name of names) {
    await picker.getByRole('searchbox').fill(name);
    await picker.getByRole('checkbox', { name, exact: true }).check();
  }
  await picker.getByRole('button', { name: 'Done', exact: true }).click();
}
async function compare(page: Page) {
  await ready(page);
  const query = new URL(page.url()).searchParams;
  query.set('selection', 'true');
  query.set('highlights', query.get('highlights') !== 'false' ? 'true' : 'false');
  if (!query.has('type')) for (const type of ['artwork', 'book', 'event']) query.append('type', type);
  const response = await page.request.get(`/api/backend/v1/atlas?${query}`);
  expect(response.ok()).toBe(true);
  const data: AtlasResponse = await response.json();
  await expect(page.locator('.all-lane > header h2')).toHaveText(data.lanes.map(lane => lane.name));
  for (const lane of data.lanes) {
    await expect(page.locator(`.all-lane:has(#all-lane-${lane.key}) > header > span`)).toHaveText(lane.total.toLocaleString('en-GB'));
    expect(lane.items.length).toBeLessThanOrEqual(60);
  }
  await expect(page.locator('.all-canvas-heading [role=status]')).toHaveText(`${data.total.toLocaleString('en-GB')} entries`);
  return data;
}

for (const [width,height] of [[1920,1080],[1440,900],[1366,768],[1280,720],[1024,768],[768,1024],[390,844],[320,800]]) test(`all starting points are visible and centered at ${width}×${height}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height });
  await page.goto('/all');
  const starts=page.locator('.all-start');
  const main=page.getByRole('group',{name:'Main starting points',exact:true});
  await expect(starts.getByRole('button')).toHaveCount(30);
  await expect(main.getByRole('button')).toHaveCount(12);
  await expect(page.getByText('More starting points',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Edo Japan', exact: true })).toBeVisible();
  for(const side of ['Earlier starting points','Later starting points'])await expect(page.getByRole('group',{name:side,exact:true}).getByRole('button')).toHaveCount(9);
  const names=await starts.getByRole('button').allTextContents();
  expect(new Set(names).size).toBe(30);
  const center=await main.boundingBox();
  expect(center).not.toBeNull();
  expect(Math.abs(center!.x+center!.width/2-width/2)).toBeLessThanOrEqual(2);
  for(const button of await starts.getByRole('button').all()){
    await expect(button).toBeVisible();
    const box=await button.boundingBox();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    expect(box!.x+box!.width).toBeLessThanOrEqual(width);
    expect(box!.height).toBeGreaterThanOrEqual(44);
    if(width>=1024){expect(box!.y).toBeGreaterThanOrEqual(0);expect(box!.y+box!.height).toBeLessThanOrEqual(height);}
  }
  if(width>=1024){
    const left=await page.getByRole('group',{name:'Earlier starting points',exact:true}).boundingBox();
    const right=await page.getByRole('group',{name:'Later starting points',exact:true}).boundingBox();
    expect(left!.x+left!.width).toBeLessThan(center!.x);
    expect(right!.x).toBeGreaterThan(center!.x+center!.width);
    const canvas=await page.locator('.all-empty-canvas').boundingBox();
    expect(Math.abs(left!.y+left!.height/2-(canvas!.y+canvas!.height/2))).toBeLessThanOrEqual(4);
  }
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  expect((await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`starting-points-${width}.png`) });
  await starts.getByRole('button', { name: 'The Enlightenment', exact: true }).click();
  await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await expect(page).toHaveURL(/preset=enlightenment/);
});

test('starting points support keyboard selection, clearing and the last mobile choice',async({page})=>{
  await page.setViewportSize({width:320,height:800});
  await page.goto('/all');
  const main=page.getByRole('group',{name:'Main starting points',exact:true});
  await expect(main.getByRole('button')).toHaveCount(12);
  await main.getByRole('button').first().focus();
  await page.keyboard.press('Enter');
  await ready(page);
  await expect(page).toHaveURL(/preset=first-world-war/);
  await page.getByRole('button',{name:'Clear',exact:true}).click();
  await expect(page.locator('.all-start button')).toHaveCount(30);
  const last=page.getByRole('button',{name:'The digital turn',exact:true});
  await last.focus();
  await expect(last).toBeInViewport();
  await page.keyboard.press('Enter');
  await ready(page);
  await expect(page).toHaveURL(/preset=digital/);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});

for (const width of [1440, 390, 320]) test(`Japan immediately shows all matching artworks, books and events at ${width}px`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/all');
  await choose(page, 'Countries', ['Japan']);
  const data = await compare(page);
  expect(data.lanes.map(lane => lane.key)).toEqual(['artwork', 'book', 'event']);
  for (const lane of data.lanes) expect(lane.total).toBeGreaterThan(0);
  await expect(page.getByRole('checkbox', { name: 'Highlights', exact: true })).toBeChecked();
  expect(new URL(page.url()).searchParams.getAll('type').sort()).toEqual(['artwork', 'book', 'event']);
  if (width < 760) await page.getByRole('button', { name: 'Filters', exact: true }).click();
  await expect(page.getByRole('button', { name: '+ Add', exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({ path: info.outputPath(`japan-${width}.png`) });
  await page.reload(); await compare(page);
});

test('countries combine, other filters intersect, and edits refresh counts and history', async ({ page }) => {
  await page.goto('/all');
  await choose(page, 'Countries', ['Japan']); const japan = await compare(page);
  await choose(page, 'Countries', ['France']); const combined = await compare(page);
  expect(combined.total).toBeGreaterThan(japan.total);
  expect(new URL(page.url()).searchParams.getAll('country').sort()).toEqual(['france','japan']);
  await choose(page, 'Continents', ['Asia']); const asia = await compare(page);
  expect(asia.total).toBeLessThan(combined.total);
  await page.getByLabel('Region', { exact: true }).selectOption('eastern-asia'); await compare(page);
  await page.getByRole('button', { name: 'Remove Eastern Asia filter', exact: true }).click(); await compare(page);
  await page.getByRole('button', { name: 'Remove Asia filter', exact: true }).click(); await compare(page);
  await page.getByRole('button', { name: 'Remove France filter', exact: true }).click();
  expect((await compare(page)).total).toBe(japan.total);
  await page.goBack(); expect((await compare(page)).total).toBe(combined.total);
  await page.goForward(); expect((await compare(page)).total).toBe(japan.total);
});

for (const query of ['country=japan', 'continent=asia', 'region=eastern-asia', 'q=Hokusai']) test(`shared ${query} links initialize all layers and remain live`, async ({ page }) => {
  await page.goto(`/all?${query}`); await compare(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await page.getByRole('searchbox', { name: 'Search the timeline' }).fill('wave'); await compare(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await page.reload(); await compare(page);
});

test('search starts the empty view and explicit Highlights remains optional', async ({ page }) => {
  await page.goto('/all');
  await page.getByRole('searchbox', { name: 'Search the timeline' }).fill('Hokusai');
  await expect(page.getByRole('checkbox', { name: 'Highlights', exact: true })).toBeChecked();
  await page.getByRole('checkbox', { name: 'Highlights', exact: true }).uncheck();
  const all = await compare(page); expect(all.total).toBeGreaterThan(0);
  await page.getByRole('checkbox', { name: 'Highlights', exact: true }).check();
  const highlights = await compare(page); expect(highlights.total).toBeLessThanOrEqual(all.total);
  await expect(page).toHaveURL(/highlights=true/);
  await page.getByRole('checkbox', { name: 'Highlights', exact: true }).uncheck();
  expect((await compare(page)).total).toBe(all.total);
  await page.getByRole('button', { name: 'Reset view', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Choose a starting point' })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: 'Highlights', exact: true })).toBeChecked();
});

async function layerChoice(dialog: Locator, label: string, name: string) {
  await dialog.locator('summary').filter({ hasText: label }).click();
  await dialog.getByRole('checkbox', { name, exact: true }).check();
  await dialog.locator('details[open]').getByRole('button', { name: 'Done', exact: true }).click();
}

test('Add restores a removed layer and keeps both global and native filters on later edits', async ({ page }) => {
  await page.goto('/all?country=japan'); const initial = await compare(page);
  await page.getByRole('button', { name: 'Remove books from timeline', exact: true }).click(); await compare(page);
  await page.getByRole('button', { name: '+ Add', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Add a layer' });
  await dialog.getByRole('button', { name: 'Books', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: 'Book highlights', exact: true })).toBeChecked();
  await expect(dialog.locator('.atlas-layer-action [role=status]')).toHaveText(`${initial.lanes.find(lane => lane.key === 'book')!.total.toLocaleString('en-GB')} matching entries`);
  await layerChoice(dialog, 'Languages', 'Japanese');
  await dialog.getByRole('button', { name: 'Add books layer', exact: true }).click(); await compare(page);
  await expect(page).toHaveURL(/book_language=/);
  const language = new URL(page.url()).searchParams.get('book_language');
  await choose(page, 'Countries', ['France']); await compare(page);
  expect(new URL(page.url()).searchParams.get('book_language')).toBe(language);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await page.getByRole('button', { name: '+ Add', exact: true }).click();
  await dialog.getByRole('button', { name: 'Books', exact: true }).click();
  await expect(dialog.locator('summary').filter({ hasText: 'Languages' })).toContainText('Japanese');
  await dialog.getByRole('button', { name: 'Close content picker', exact: true }).click();
  await page.reload(); await compare(page);
});

test('removed layers stay removed until Add or a new filter starts the empty view', async ({ page }) => {
  await page.goto('/all?country=japan'); await ready(page);
  await page.getByRole('button', { name: 'Remove books from timeline', exact: true }).click(); await ready(page);
  await choose(page, 'Countries', ['France']); await compare(page);
  await expect(page.locator('.all-lane > header h2')).toHaveText(['Artworks','Events']);
  await page.getByRole('button', { name: 'Remove artworks from timeline', exact: true }).click();
  await page.getByRole('button', { name: 'Remove events from timeline', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Choose a starting point' })).toBeVisible();
  await page.reload(); await expect(page.getByRole('heading', { name: 'Choose a starting point' })).toBeVisible();
  await choose(page, 'Continents', ['Asia']); await compare(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});

test('a late Japan response cannot replace a newer combined filter', async ({ page }) => {
  await page.goto('/all');
  let release!: () => void; const gate = new Promise<void>(resolve => { release = resolve; });
  let held = false;
  await page.route('**/api/backend/v1/atlas?*', async route => {
    const countries = new URL(route.request().url()).searchParams.getAll('country');
    if (countries.length !== 1 || countries[0] !== 'japan') { await route.continue(); return; }
    const response = await route.fetch(); held = true; await gate;
    await route.fulfill({ response }).catch(() => {});
  });
  try {
    await choose(page, 'Countries', ['Japan']); await expect.poll(() => held).toBe(true);
    await expect(page.locator('.all-canvas-heading .loading-spinner')).toBeVisible();
    await choose(page, 'Countries', ['France']); await compare(page);
  } finally { release(); await page.unrouteAll({ behavior: 'wait' }); }
  await compare(page);
  expect(new URL(page.url()).searchParams.getAll('country').sort()).toEqual(['france','japan']);
});
