import { expect, test, type Page } from '@playwright/test';

const atlasURL = '**/api/backend/v1/atlas?*';
const startURL = '/all?selection=true&type=artwork&type=book&type=event&start=1900&end=1940';
test.afterEach(async ({ page }) => { await page.unrouteAll({ behavior: 'ignoreErrors' }); });
async function ready(page: Page) {
  await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toHaveCount(0);
}
const ticks = (page: Page) => page.locator('.tick-row > span').evaluateAll(nodes => nodes.map(node => ({ label: node.textContent, left: (node as HTMLElement).style.left })));

// Delay real read-only responses: no invented catalogue entries or database writes.
async function holdResponses(page: Page, matches: (url: URL) => boolean = () => true) {
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  const held: string[] = [], settled: string[] = [];
  await page.route(atlasURL, async route => {
    const url = new URL(route.request().url());
    if (!matches(url)) { await route.continue(); return; }
    const response = await route.fetch();
    held.push(url.toString());
    await gate;
    await route.fulfill({ response }).catch(() => {}); // A superseded request may already be aborted.
    settled.push(url.toString());
  });
  return { release, held, settled };
}

test('slow responses do not snap back the range or lose repeated year clicks', async ({ page }) => {
  await page.goto(startURL); await ready(page);
  const initialTicks = await ticks(page);
  const held = await holdResponses(page);
  try {
    const later = page.getByRole('button', { name: 'Move range 1 year later', exact: true });
    await later.click();
    await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1901', { timeout: 700 });
    await expect(page.locator('.all-canvas-heading .loading-spinner')).toBeVisible();
    await later.click(); await later.click();
    await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1903');
    await expect(page.getByLabel('All end year', { exact: true })).toHaveValue('1943');
    await expect(page).toHaveURL(/start=1903/);
    expect(await ticks(page)).toEqual(initialTicks);
    await expect.poll(() => held.held.some(url => new URL(url).searchParams.get('start') === '1903')).toBe(true);
  } finally { held.release(); }
  await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1903');
  await expect(page.locator('.all-canvas-heading .loading-spinner')).toHaveCount(0);
});

test('dragging commits immediately, keeps the axis fixed and survives a newer response', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&start=1500&end=1800'); await ready(page);
  const initialTicks = await ticks(page), initialURL = page.url();
  const held = await holdResponses(page, url => url.searchParams.get('end') !== '1950');
  try {
    const band = page.getByRole('button', { name: 'Move selected time range', exact: true });
    const before = (await band.boundingBox())!, track = (await page.locator('.range-track').boundingBox())!;
    const x = before.x + before.width / 2, y = track.y + track.height / 2;
    await page.mouse.move(x, y); await page.mouse.down();
    await page.mouse.move(x + track.width * .12, y, { steps: 8 });
    expect(page.url()).toBe(initialURL);
    await expect(page.locator('.all-canvas-heading h1')).not.toContainText('1500');
    const preview = (await band.boundingBox())!;
    await page.mouse.up();
    await expect(page).not.toHaveURL(initialURL);
    expect(Math.abs((await band.boundingBox())!.x - preview.x)).toBeLessThan(2);
    expect(Math.abs((await band.boundingBox())!.width - before.width)).toBeLessThan(2);
    await expect.poll(() => held.held.length).toBeGreaterThan(0);
    await page.getByLabel('All start year', { exact: true }).fill('1900');
    await page.getByLabel('All end year', { exact: true }).fill('1950');
    await page.getByLabel('All end year', { exact: true }).press('Enter');
    await ready(page);
  } finally { held.release(); }
  await expect.poll(() => held.settled.length).toBe(held.held.length);
  await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1900');
  await expect(page.getByLabel('All end year', { exact: true })).toHaveValue('1950');
  expect(await ticks(page)).toEqual(initialTicks);
  await page.goBack(); await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).not.toHaveValue('1900');
});

test('a failed request can retry with a spinner and leaves year controls usable', async ({ page }) => {
  await page.goto(startURL); await ready(page);
  await page.route(atlasURL, route => route.fulfill({ status: 503, json: { error: { message: 'Connection interrupted' } } }));
  await page.getByRole('button', { name: 'Move range 1 year later', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toBeVisible();
  await expect(page.getByLabel('All start year', { exact: true })).toBeEnabled();
  await page.unroute(atlasURL);
  const held = await holdResponses(page);
  try {
    await page.getByRole('button', { name: 'Retry', exact: true }).click();
    await expect(page.locator('.all-canvas-heading .loading-spinner')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toHaveCount(0);
    await expect.poll(() => held.held.length).toBeGreaterThan(0);
  } finally { held.release(); }
  await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});

test('removing a layer and resetting while loading cannot restore old entries', async ({ page }) => {
  await page.goto(startURL); await ready(page);
  const held = await holdResponses(page);
  try {
    await page.getByRole('button', { name: 'Move range 1 year later', exact: true }).click();
    await expect.poll(() => held.held.length).toBeGreaterThan(0);
    await page.getByRole('button', { name: 'Remove books from timeline', exact: true }).click();
    await expect(page.locator('#all-lane-book')).toHaveCount(0, { timeout: 700 });
    await page.getByRole('button', { name: 'Clear', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Choose a starting point' })).toBeVisible();
  } finally { held.release(); }
  await expect(page.locator('.all-lane,.all-canvas-heading .loading-spinner')).toHaveCount(0);
  await page.getByRole('button', { name: 'The First World War', exact: true }).click(); await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1910');
});

test('updating a layer keeps the visible global search and region and matches its preview count', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&start=1800&end=1950&q=Madame&region=western-europe'); await ready(page);
  await page.getByRole('button', { name: '+ Add', exact: true }).click();
  const panel = page.getByRole('dialog', { name: 'Add a layer' });
  await panel.getByRole('button', { name: 'Books', exact: true }).click();
  const expected = await (await page.request.get('/api/backend/v1/atlas?type=book&start=1800&end=1950&q=Madame&region=western-europe&book_top100=true&limit=1')).json();
  expect(expected.total).toBeGreaterThan(0);
  await expect(panel.locator('.atlas-layer-action [role=status]')).toHaveText(`${expected.total.toLocaleString('en-GB')} matching entries`);
  await panel.getByRole('button', { name: 'Update books layer', exact: true }).click(); await ready(page);
  await expect(page).toHaveURL(/q=Madame/); await expect(page).toHaveURL(/region=western-europe/);
  await expect(page.locator('.all-canvas-heading [role=status]')).toHaveText(`${expected.total} entries`);
});

for (const width of [1440, 390, 320]) test(`crowded periods have visible bars and legible counts at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/all?preset=first-world-war'); await ready(page);
  const columns = page.locator('.all-lane .period-column');
  expect(await columns.count()).toBeGreaterThan(1);
  const geometry = await columns.evaluateAll(nodes => nodes.map(node => {
    const bar = node.querySelector('.period-bar')!.getBoundingClientRect();
    const count = node.querySelector('.period-count')!;
    const style = getComputedStyle(count), text = document.createRange();
    text.selectNodeContents(count);
    const rect = text.getBoundingClientRect();
    return { bar: { width: bar.width, height: bar.height }, count: { left: rect.left, right: rect.right, visible: style.visibility !== 'hidden' && style.display !== 'none' }, total: Number(count.textContent) };
  }));
  for (const item of geometry.filter(item => item.total > 0)) {
    expect(item.bar.width).toBeGreaterThan(0); expect(item.bar.height).toBeGreaterThan(0);
  }
  if (width > 760) {
    const visible = geometry.filter(item => item.count.visible);
    for (let i = 1; i < visible.length; i++) expect(visible[i].count.left).toBeGreaterThanOrEqual(visible[i - 1].count.right);
  }
  await columns.first().focus();
  await expect(page.locator('.all-lane .overview-caption p').first()).not.toContainText('Choose a period');
  await page.keyboard.press('ArrowRight'); await expect(columns.nth(1)).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({ path: info.outputPath(`crowded-${width}.png`) });
});

test('year fields remain reachable with filters open on a short phone screen', async ({ page }, info) => {
  await page.setViewportSize({ width: 320, height: 568 });
  await page.goto('/all?preset=first-world-war'); await ready(page);
  await page.getByRole('button', { name: 'Filters', exact: true }).click();
  const from = page.getByLabel('All start year', { exact: true }), to = page.getByLabel('All end year', { exact: true });
  await from.scrollIntoViewIfNeeded();
  await expect(from).toBeInViewport();
  await from.fill('1900'); await from.press('Tab');
  await expect(to).toBeFocused(); await to.fill('1945'); await to.press('Enter'); await ready(page);
  await expect(page).toHaveURL(/start=1900&end=1945/);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await expect(to).toBeInViewport();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await page.screenshot({ path: info.outputPath('short-phone-years.png') });
});

test('BCE keyboard movement, empty ancient years, cutoff and invalid shared ranges recover', async ({ page }) => {
  await page.goto('/all?selection=true&type=artwork&type=book&type=event&start=-2&end=2'); await ready(page);
  const handle = page.getByLabel('Timeline start handle', { exact: true });
  await handle.focus(); await handle.press('ArrowRight');
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('-1');
  await handle.press('ArrowRight');
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1');
  await ready(page);
  const from = page.getByLabel('All start year', { exact: true }), to = page.getByLabel('All end year', { exact: true });
  await from.fill('-12000'); await to.fill('-11999'); await to.press('Enter'); await ready(page);
  await expect(page.locator('.all-canvas-heading [role=status]')).toHaveText('0 entries');
  await expect(page.getByRole('button', { name: 'Move range 1 year earlier', exact: true })).toBeDisabled();
  await from.fill('1971'); await to.fill('2000'); await to.press('Enter'); await ready(page);
  await expect(page.locator('.all-lane').first()).toContainText('Artworks end at 1970.');
  await expect(page.getByRole('button', { name: 'Move range 1 year later', exact: true })).toBeDisabled();
  await page.goto('/all?selection=true&type=book&start=bad&end=2001');
  await expect(page.getByRole('heading', { name: 'We couldn’t load this view' })).toBeVisible();
  await expect(from).not.toHaveValue('NaN');
  await from.fill('1800'); await to.fill('1900'); await to.press('Enter'); await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(1);
});

test('Add uses the newest years while the timeline is still loading and shows its own spinner', async ({ page }) => {
  await page.goto(startURL); await ready(page);
  const held = await holdResponses(page);
  try {
    await page.getByRole('button', { name: 'Move range 1 year later', exact: true }).click();
    await page.getByRole('button', { name: '+ Add', exact: true }).click();
    const panel = page.getByRole('dialog', { name: 'Add a layer' });
    await panel.getByRole('button', { name: 'Books', exact: true }).click();
    await expect(panel.locator('.atlas-layer-action .loading-spinner')).toBeVisible();
    await expect(panel.getByRole('button', { name: 'Update books layer', exact: true })).toBeDisabled();
    await expect.poll(() => held.held.some(value => {
      const p = new URL(value).searchParams;
      return p.get('limit') === '1' && p.get('type') === 'book' && p.get('start') === '1901' && p.get('end') === '1941';
    })).toBe(true);
  } finally { held.release(); }
  const panel = page.getByRole('dialog', { name: 'Add a layer' });
  await panel.getByRole('button', { name: 'Update books layer', exact: true }).click(); await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1901');
  await expect(page.getByLabel('All end year', { exact: true })).toHaveValue('1941');
});

for (const [kind, resource, retryLabel] of [
  ['books', 'books', 'Retry book'], ['events', 'events', 'Retry event'], ['artworks', 'atlas/artworks', 'Retry artwork'],
] as const) test(`${kind} details show loading feedback on open and retry`, async ({ page }) => {
  await page.goto('/all?preset=first-world-war'); await ready(page);
  await page.getByRole('button', { name: `Browse ${kind}`, exact: true }).click();
  const browse = page.getByRole('dialog', { name: `Browse ${kind}`, exact: true });
  await expect(browse.getByRole('button', { name: /^Read / }).first()).toBeVisible();
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let failReply!: () => void;
  const failureGate = new Promise<void>(resolve => { failReply = resolve; });
  let fail = true;
  await page.route(`**/api/backend/v1/${resource}/*`, async route => {
    if (fail) { await failureGate; await route.fulfill({ status: 503, json: { error: { message: 'Connection interrupted' } } }); return; }
    const response = await route.fetch(); await gate; await route.fulfill({ response });
  });
  await browse.getByRole('button', { name: /^Read / }).first().click();
  try { await expect(page.getByRole('dialog').locator('.loading-spinner')).toBeVisible(); }
  finally { failReply(); }
  const retry = page.getByRole('button', { name: retryLabel, exact: true });
  await expect(retry).toBeVisible(); fail = false;
  try {
    await retry.click();
    await expect(page.getByRole('dialog').locator('.loading-spinner')).toBeVisible();
    await expect(retry).toHaveCount(0);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await expect(page.getByRole('dialog').locator('.loading-spinner')).toHaveCSS('animation-name', 'none');
  } finally { release(); }
  await expect(page.getByRole('dialog').locator('.loading-spinner')).toHaveCount(0, { timeout: 20000 });
  await expect(page.getByRole('dialog').getByRole('heading').first()).toBeVisible();
  await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('button', { name: `Browse ${kind}`, exact: true })).toBeFocused();
});
