import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const zoomOut = (page: Page) => page.getByRole('button', { name: 'Zoom out to all years', exact: true });
const start = (page: Page) => page.getByLabel('All start year', { exact: true });
const end = (page: Page) => page.getByLabel('All end year', { exact: true });
const tickState = (page: Page) => page.locator('.all-explorer .tick-row > span').evaluateAll(nodes => nodes.map(node => ({ label: node.textContent, left: (node as HTMLElement).style.left })));
const label = (year: number) => year < 0 ? `${Math.abs(year)} BCE` : String(year);
async function ready(page: Page) {
  await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('.all-explorer').getByRole('alert')).toHaveCount(0);
}
async function fitted(page: Page, from: number, to: number) {
  await expect(start(page)).toHaveValue(String(from));
  await expect(end(page)).toHaveValue(String(to));
  const ticks = await tickState(page);
  expect(ticks[0]).toEqual({ label: label(from), left: '0%' });
  expect(ticks.at(-1)).toEqual({ label: label(to), left: '100%' });
  expect(ticks.every(tick => Number.parseFloat(tick.left) >= 0 && Number.parseFloat(tick.left) <= 100)).toBe(true);
  await expect(zoomOut(page)).toBeEnabled();
}
async function overview(page: Page) {
  await expect(start(page)).toHaveValue('-12000');
  await expect(end(page)).toHaveValue('2000');
  await expect(zoomOut(page)).toBeDisabled();
  expect((await tickState(page)).map(tick => tick.label)).toEqual(expect.arrayContaining(['BCE', '1400', '2000']));
  await expect(page).not.toHaveURL(/preset=|window=|start=|end=/);
}

for (const width of [1440, 390, 320]) {
  for (const [name, from, to, mainFrom, mainTo] of [
    ['The Second World War', 1933, 1955, 1939, 1945],
    ['The Renaissance', 1300, 1650, 1350, 1600],
  ] as const) test(`${name} fills the timeline at ${width}px and zooms back out`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/all');
    await expect(zoomOut(page)).toHaveCount(0);
    await page.getByRole('button', { name, exact: true }).click();
    await ready(page); await fitted(page, from, to);
    await expect(page.locator('.all-lane')).toHaveCount(3);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await expect(zoomOut(page)).toBeInViewport();
    expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
    await page.screenshot({ path: info.outputPath(`focused-${width}.png`) });
    await zoomOut(page).focus(); await zoomOut(page).press('Enter');
    await ready(page); await overview(page);
    await expect(page.locator('.all-lane')).toHaveCount(3);
    await page.goBack(); await ready(page); await fitted(page, from, to);
    const periodURL = new URL(page.url());
    periodURL.searchParams.set('window', 'period');
    await page.goto(periodURL.toString());
    await ready(page); await fitted(page, mainFrom, mainTo);
    await page.reload(); await ready(page); await fitted(page, mainFrom, mainTo);
  });
}

for (const [from, to] of [[-12000, -11999], [-500, -100], [-1, 1], [1, 2], [1399, 1401], [1999, 2000]]) {
  test(`custom interval ${from} to ${to} fits both endpoints and resets`, async ({ page }) => {
    await page.goto('/all?selection=true&type=event'); await ready(page); await overview(page);
    await start(page).fill(String(from)); await end(page).fill(String(to)); await end(page).press('Enter');
    await ready(page); await fitted(page, from, to);
    expect((await tickState(page)).some(tick => tick.label === '0')).toBe(false);
    await page.reload(); await ready(page); await fitted(page, from, to);
    await zoomOut(page).click(); await ready(page); await overview(page);
    await expect(page.locator('.all-lane > header h2')).toHaveText(['Events']);
  });
}

test('zoom out preserves layers, search, geography, highlights and entity filters', async ({ page }) => {
  const filters = 'selection=true&type=book&q=Madame&country=france&continent=europe&region=western-europe&highlights=false&book_language=Q150&book_top100=false';
  await page.goto(`/all?${filters}&preset=renaissance`); await ready(page);
  await zoomOut(page).click(); await ready(page); await overview(page);
  const params = new URL(page.url()).searchParams;
  for (const [key, value] of new URLSearchParams(filters)) expect(params.getAll(key)).toContain(value);
  await expect(page.locator('.all-lane > header h2')).toHaveText(['Books']);
  await page.goBack(); await ready(page); await fitted(page, 1300, 1650);
  await page.goForward(); await ready(page); await overview(page);
  await page.reload(); await ready(page); await overview(page);
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('searchbox', { name: 'Search historical period' }).fill('second world');
  await picker.getByRole('radio', { name: 'The Second World War', exact: true }).check();
  await picker.getByRole('button', { name: 'Done', exact: true }).click();
  await ready(page); await fitted(page, 1933, 1955);
  for (const [key, value] of new URLSearchParams(filters)) expect(new URL(page.url()).searchParams.getAll(key)).toContain(value);
});

test('density drill-down refits every lane, including history navigation', async ({ page }) => {
  await page.goto('/all?preset=renaissance'); await ready(page);
  await page.locator('.all-artwork-density summary').click();
  const period = page.locator('.all-lane').first().getByRole('button', { name: /^Explore / }).first();
  await period.click(); await ready(page);
  const from = Number(await start(page).inputValue()), to = Number(await end(page).inputValue());
  expect(to - from).toBeLessThan(350);
  await fitted(page, from, to);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await page.goBack(); await ready(page); await fitted(page, 1300, 1650);
  await page.goForward(); await ready(page); await fitted(page, from, to);
});

test('slider previews without requests, then fits the committed interval', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&start=1300&end=1600'); await ready(page);
  const before = await tickState(page), beforeURL = page.url();
  const requests: string[] = [];
  page.on('request', request => { if (request.url().includes('/api/backend/v1/atlas?')) requests.push(request.url()); });
  const band = page.getByRole('button', { name: 'Move selected time range', exact: true });
  const box = (await band.boundingBox())!, track = (await page.locator('.range-track').boundingBox())!;
  const x = box.x + box.width / 2, y = track.y + track.height / 2;
  await page.mouse.move(x, y); await page.mouse.down();
  await page.mouse.move(x + track.width * .1, y, { steps: 6 });
  expect(page.url()).toBe(beforeURL); expect(requests).toHaveLength(0);
  expect(await tickState(page)).toEqual(before);
  expect(Math.abs((await band.boundingBox())!.width - box.width)).toBeLessThan(1);
  await page.mouse.up(); await ready(page);
  await fitted(page, Number(await start(page).inputValue()), Number(await end(page).inputValue()));
  expect(await tickState(page)).not.toEqual(before);
  await zoomOut(page).click(); await ready(page); await overview(page);
});

test('a late interval response cannot undo zoom out or restore old geometry', async ({ page }) => {
  await page.goto('/all?preset=second-world-war'); await ready(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let held = false;
  await page.route('**/api/backend/v1/atlas?*', async route => {
    if (!new URL(route.request().url()).searchParams.has('start')) { await route.continue(); return; }
    const response = await route.fetch(); held = true; await gate;
    await route.fulfill({ response }).catch(() => {});
  });
  try {
    await start(page).fill('1939'); await end(page).fill('1945'); await end(page).press('Enter');
    await expect.poll(() => held).toBe(true);
    await fitted(page, 1939, 1945);
    await expect(page.locator('.all-lane .period-column,.all-lane .timeline-mark')).toHaveCount(0);
    await zoomOut(page).click(); await ready(page); await overview(page);
  } finally { release(); await page.unrouteAll({ behavior: 'wait' }); }
  await overview(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});

test('zoom out recovers from a failed or invalid interval request', async ({ page }) => {
  await page.goto('/all?preset=second-world-war'); await ready(page);
  await page.route('**/api/backend/v1/atlas?*', route => {
    if (new URL(route.request().url()).searchParams.has('start')) return route.fulfill({ status: 503, json: { error: { message: 'Connection interrupted' } } });
    return route.continue();
  });
  await page.getByRole('button', { name: 'Move range 1 year later', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toBeVisible();
  await zoomOut(page).click(); await ready(page); await overview(page);
  await page.unrouteAll({ behavior: 'wait' });
  await page.goto('/all?selection=true&type=book&start=bad&end=2001');
  await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toBeVisible();
  await expect(zoomOut(page)).toBeEnabled();
  await zoomOut(page).click(); await ready(page); await overview(page);
});

test('focused ticks stay inside the canvas and do not overlap after resizing', async ({ page }) => {
  await page.goto('/all?preset=renaissance'); await ready(page);
  for (const width of [1920, 1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await fitted(page, 1300, 1650);
    await expect.poll(async () => {
      const geometry = await page.locator('.tick-row > span').evaluateAll(nodes => nodes.map(node => {
        const range = document.createRange(); range.selectNodeContents(node);
        const rect = range.getBoundingClientRect(); return { left: rect.left, right: rect.right };
      }));
      return geometry.every((rect, index) => rect.left >= 0 && rect.right <= width && (index === 0 || rect.left > geometry[index - 1].right));
    }).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

// Explicit overview URLs should not offer another zoom-out step.
test('all-years URLs disable zoom out; Clear still returns to the starting point', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&start=-12000&end=2000'); await ready(page);
  await expect(zoomOut(page)).toBeDisabled();
  await page.getByRole('button', { name: 'Clear', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Explore a moment in history' })).toBeVisible();
  await expect(zoomOut(page)).toHaveCount(0);
});
