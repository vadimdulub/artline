import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function ready(page: Page) {
  await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('.all-explorer').getByRole('alert')).toHaveCount(0);
}
for (const width of [1440, 390, 320]) test(`illustrated starting points and direct artwork access at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 1000 });
  const writes: string[] = [];
  page.on('request', r => { if (r.url().includes('/api/') && r.method() !== 'GET') writes.push(r.url()); });
  await page.goto('/all');
  await expect(page.getByRole('heading', { name: 'Explore a moment in history' })).toBeVisible();
  await expect(page.getByRole('button', { name: '+ Add', exact: true })).toHaveCount(0);
  await expect(page.locator('.all-start button')).toHaveCount(32);
  await expect(page.locator('.all-start-card img')).toHaveCount(4);
  await expect.poll(() => page.locator('.all-start-card img').evaluateAll(nodes => nodes.every(node => (node as HTMLImageElement).complete && (node as HTMLImageElement).naturalWidth > 0))).toBe(true);
  await expect(page.locator('.all-start-card').first()).toContainText('Italy & Northern Europe');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`starting-${width}.png`) });
  await page.getByRole('button', { name: 'The Renaissance', exact: true }).click();
  await ready(page);
  await expect(page.locator('.all-artwork-card')).toHaveCount(150);
  await expect(page.locator('.all-artwork-card').first()).toBeInViewport();
  await expect(page.locator('.all-artwork-card img').first()).toBeVisible();
  await expect(page.locator('.all-lane')).toHaveCount(3);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`renaissance-${width}.png`) });
  await page.locator('.all-artwork-card').first().click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.locator('.all-artwork-card').first()).toBeFocused();
  expect(writes).toEqual([]);
});

test('World War II starts with explicit removable countries and survives history', async ({ page }) => {
  await page.goto('/all');
  await page.getByRole('button', { name: 'The Second World War', exact: true }).click();
  await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual(['china', 'france', 'germany', 'japan', 'soviet union', 'united kingdom']);
  await expect(page.locator('.all-view-context')).toContainText('Artwork focus: 6 countries');
  await expect(page.locator('.all-artwork-card').first()).toBeVisible();
  await page.reload(); await ready(page);
  await page.locator('.all-view-context > summary').click();
  await page.getByRole('button', { name: 'Show all countries', exact: true }).click(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual([]);
  await expect(page).toHaveURL(/preset=second-world-war/);
  await page.goBack(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toHaveLength(6);
});

test('one creator filter combines painter and author identities and can be cleared', async ({ page }) => {
  await page.goto('/all');
  const filter = page.locator('.multi-filter').filter({ has: page.locator('summary', { hasText: 'Creators' }) });
  await filter.locator('summary').click();
  await filter.getByRole('searchbox', { name: 'Search creators', exact: true }).fill('Monet');
  const painter = filter.getByRole('checkbox', { name: 'Claude Monet · Painter', exact: true });
  await painter.check();
  await filter.getByRole('searchbox', { name: 'Search creators', exact: true }).fill('Tolstoy');
  await filter.getByRole('checkbox', { name: 'Leo Tolstoy · Author', exact: true }).check();
  await filter.getByRole('button', { name: 'Done', exact: true }).click();
  await ready(page);
  const params = new URL(page.url()).searchParams;
  expect(params.getAll('creator').some(id => id.startsWith('painter:'))).toBe(true);
  expect(params.getAll('creator').some(id => id.startsWith('author:'))).toBe(true);
  await expect(page.locator('.all-artwork-card').first()).toContainText('Claude Monet');
  await expect(page.locator('.all-lane').nth(1)).toContainText('Leo Tolstoy');
  await expect(page.locator('.all-view-context')).toContainText('events for context');
  await page.reload(); await ready(page);
  await expect(page.getByRole('button', { name: 'Remove Claude Monet · Painter filter', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Remove Leo Tolstoy · Author filter', exact: true }).click(); await ready(page);
  await expect(page.locator('.all-lane').nth(1)).toContainText('No dated books match these filters');
  await page.getByRole('button', { name: 'Show starting points', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Explore a moment in history' })).toBeVisible();
  expect(new URL(page.url()).searchParams.getAll('creator')).toEqual([]);
});

test('artwork pages stay bounded and Browse starts in the same filter scope', async ({ page }) => {
  await page.goto('/all?preset=renaissance'); await ready(page);
  const first = await page.locator('.all-artwork-card').first().getAttribute('aria-label');
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.locator('.all-artwork-card')).toHaveCount(300);
  await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('aria-label', first!);
  await page.reload(); await ready(page);
  await page.getByRole('button', { name: 'Artworks', exact: true }).click();
  const panel = page.getByRole('dialog', { name: 'Browse artworks', exact: true });
  await expect(panel.locator('.atlas-picker-list li')).toHaveCount(31);
  await page.keyboard.press('Escape');
  await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('aria-label', first!);
  await page.getByRole('checkbox', { name: 'Books', exact: true }).uncheck(); await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(2);
  await page.getByRole('checkbox', { name: 'Books', exact: true }).check(); await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});
