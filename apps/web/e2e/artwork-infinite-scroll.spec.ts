import { expect, test, type Page } from '@playwright/test';

const painters = '/?view=paintings&popular=false&start=1800&end=1950';
async function ready(page: Page) {
  await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.all-artwork-card')).toHaveCount(150);
}
async function scrollEnd(page: Page, last: number) {
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.locator('.all-artwork-strip li[aria-posinset]').last()).toHaveAttribute('aria-posinset', String(last));
  await expect(page.locator('.all-artwork-strip')).toHaveAttribute('aria-busy', 'false');
}

test('a short final artwork page stops requesting more records', async ({ page }) => {
  await page.goto(painters + '&painter=claude-monet'); await ready(page);
  await scrollEnd(page, 213);
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.locator('.all-gallery [role=status]')).toHaveText('All artworks loaded');
  await expect(page.locator('.all-artwork-card')).toHaveCount(213);
});
for (const width of [1440, 390]) for (const [name, url] of [['Painters', painters], ['All', '/all?preset=renaissance']]) {
  test(`${name} scrolls forward and back through bounded artwork windows at ${width}`, async ({ page }, info) => {
    await page.setViewportSize({ width, height: 1000 });
    const cursors: string[] = [];
    page.on('request', request => { const q = new URL(request.url()).searchParams; if (request.url().includes('/v1/atlas?') && q.has('after_artwork')) cursors.push(q.get('after_artwork')!); });
    await page.goto(url); await ready(page);
    expect(cursors).toHaveLength(0);
    const first = await page.locator('.all-artwork-card').first().getAttribute('aria-label');
    await expect(page.getByText(/ordered by creation date/)).toHaveCount(0);
    await scrollEnd(page, 300);
    const retainedPosition = await page.locator('.all-artwork-strip').evaluate(el => el.scrollLeft);
    expect(retainedPosition).toBeGreaterThan(1000);
    await scrollEnd(page, 450);
    await scrollEnd(page, 600);
    expect(await page.locator('.all-artwork-card').count()).toBeLessThanOrEqual(450);
    expect(cursors).toHaveLength(3);
    await expect(page.locator('.all-artwork-strip li[aria-posinset]').first()).toHaveAttribute('aria-posinset', '151');
    expect(await page.locator('.all-artwork-card').evaluateAll(nodes => new Set(nodes.map(n => n.getAttribute('data-artwork-id'))).size === nodes.length)).toBe(true);
    // Returning to an evicted page refetches it without moving the scrollbar.
    await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = 0; });
    await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('aria-label', first!);
    await expect(page.locator('.all-artwork-card').first()).toBeInViewport();
    await expect(page.locator('.all-artwork-strip')).toHaveAttribute('aria-busy', 'false');
    expect(await page.locator('.all-artwork-card').count()).toBeLessThanOrEqual(450);
    await page.locator('.all-artwork-card').first().click();
    await expect(page.getByRole('dialog', { name: 'Artwork details', exact: true })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('.all-artwork-card').first()).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.screenshot({ path: info.outputPath(`infinite-${name}-${width}.png`) });
  });
}

test('an incremental failure retains paintings and retries the same page only on request', async ({ page }) => {
  await page.goto(painters); await ready(page);
  let calls = 0;
  await page.route('**/api/backend/v1/atlas?*', async route => {
    if (!new URL(route.request().url()).searchParams.has('after_artwork')) return route.continue();
    calls++;
    if (calls === 1) return route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":{"message":"Temporary failure"}}' });
    await route.continue();
  });
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.getByText('Couldn’t load more artworks.', { exact: true })).toBeVisible();
  await expect(page.locator('.all-artwork-card')).toHaveCount(150);
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft -= 2; });
  expect(calls).toBe(1);
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(page.locator('.all-artwork-card')).toHaveCount(300);
  expect(calls).toBe(2);
});

test('changing filters ignores a late incremental response', async ({ page }) => {
  await page.goto(painters); await ready(page);
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  let held = false;
  await page.route('**/api/backend/v1/atlas?*', async route => {
    if (!new URL(route.request().url()).searchParams.has('after_artwork')) return route.continue();
    const response = await route.fetch(); held = true; await gate;
    await route.fulfill({ response }).catch(() => {});
  });
  try {
    await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
    await expect.poll(() => held).toBe(true);
    await page.getByRole('searchbox').first().fill('Water Lilies');
    await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false');
    await expect(page.locator('.all-artwork-card').first()).toContainText('Water Lilies');
  } finally { release(); await page.unrouteAll({ behavior: 'wait' }); }
  await expect(page.locator('.all-artwork-card').first()).toContainText('Water Lilies');
  expect(await page.locator('.all-artwork-strip').evaluate(el => el.scrollLeft)).toBe(0);
});
