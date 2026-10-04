import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { AtlasResponse } from '../lib/atlas';

async function ready(page: Page) {
  await expect(page.locator('.painter-paintings .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('main').getByRole('alert')).toHaveCount(0);
}
for (const width of [1440, 390]) test(`Painters switches to the All artwork gallery at ${width}`, async ({ page, request }, info) => {
  await page.setViewportSize({ width, height: 1000 });
  // Old links must not silently keep the removed highlights filter active.
  await page.goto('/?painter=claude-monet&popular=false&start=1800&end=1950' + (width === 390 ? '&painting_highlights=true' : ''));
  await page.getByRole('button', { name: 'Paintings', exact: true }).click(); await ready(page);
  await expect(page.getByRole('button', { name: 'Paintings', exact: true })).toHaveAttribute('aria-pressed', 'true');
  expect((await page.locator('.painter-view-switch').boundingBox())!.height).toBeLessThan(40);
  await expect(page.locator('.painting-view-guidance')).toHaveCount(0);
  await expect(page.getByRole('checkbox', { name: 'Artwork highlights', exact: true })).toHaveCount(0);
  await expect(page.getByText(/ordered by creation date/)).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Reset view', exact: true })).toBeVisible();
  await expect(page.locator('.all-artwork-card').first()).toBeVisible();
  await expect(page.locator('.all-artwork-card').first()).toContainText('Claude Monet');
  const response = await request.get('/api/backend/v1/atlas?type=artwork&start=1800&end=1950&artwork_painter=claude-monet&artwork_popular=false&highlights=false&artwork_image_only=true');
  expect(response.ok()).toBe(true);
  const all = await response.json() as AtlasResponse;
  await expect(page.locator('.painter-paintings .timeline-counter')).toHaveText(`${all.total.toLocaleString('en-GB')} artworks`);
  await expect(page.locator('.all-artwork-card strong')).toHaveText(all.lanes[0].items.map(item => item.title));
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`paintings-${width}.png`) });
  await page.locator('.all-artwork-card').first().click();
  const dialog = page.getByRole('dialog', { name: 'Artwork details', exact: true });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Next artwork', exact: true })).toBeEnabled();
  await page.keyboard.press('Escape');
  await expect(page.locator('.all-artwork-card').first()).toBeFocused();
  await page.reload(); await ready(page);
  await page.getByRole('button', { name: 'Painter lifespans', exact: true }).click();
  await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false');
  await expect(page.locator('.artist-mark').first()).toBeVisible();
  await expect(page).toHaveURL(/painter=claude-monet/);
  await page.goBack(); await ready(page);
});

test('painting pagination resets on filter changes and observes creation cutoff', async ({ page }) => {
  await page.goto('/?view=paintings&painter=claude-monet&popular=false&start=1800&end=1950'); await ready(page);
  const first = await page.locator('.all-artwork-card').first().getAttribute('aria-label');
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.locator('.all-artwork-card')).toHaveCount(213);
  await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('aria-label', first!);
  await page.getByRole('checkbox', { name: 'Top 100 painters', exact: true }).check(); await ready(page);
  expect(new URL(page.url()).searchParams.has('painting_after')).toBe(false);
  await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('aria-label', first!);
  await page.locator('.all-artwork-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.locator('.all-artwork-card')).toHaveCount(213);
  await page.getByRole('searchbox').first().fill('Water Lilies'); await ready(page);
  expect(new URL(page.url()).searchParams.has('painting_after')).toBe(false);
  await expect(page.locator('.all-artwork-card').first()).toContainText('Water Lilies');
  await page.getByLabel('Start year', { exact: true }).fill('1971');
  await page.getByLabel('End year', { exact: true }).fill('2000');
  await page.getByLabel('End year', { exact: true }).press('Enter'); await ready(page);
  await expect(page.getByRole('heading', { name: 'No paintings in this view', exact: true })).toBeVisible();
  await expect(page.locator('.painter-paintings')).toContainText('Artwork coverage ends at 1970');
});
