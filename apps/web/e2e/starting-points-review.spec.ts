import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import type { AtlasMetadata, AtlasResponse } from '../lib/atlas';

async function ready(page: Page) {
  await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('main').getByRole('alert')).toHaveCount(0);
}

for (const width of [1440, 390]) test(`the entire starting list stays on black at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/all');
  await expect(page.getByRole('button', { name: 'Show starting points', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reset view', exact: true })).toHaveCount(0);
  await expect(page.locator('.all-start button')).toHaveCount(30);
  const last = page.getByRole('button', { name: 'The digital turn', exact: true });
  await last.scrollIntoViewIfNeeded();
  const canvas = await page.locator('.all-empty-canvas').boundingBox();
  const button = await last.boundingBox();
  expect(canvas!.y + canvas!.height).toBeGreaterThanOrEqual(button!.y + button!.height);
  await expect(page.locator('.all-empty-canvas')).toHaveCSS('background-color', 'rgb(18, 17, 15)');
  await expect(last).toContainText('Worldwide');
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`more-starting-points-${width}.png`) });
  await page.goto('/books');
  await expect(page.getByRole('button', { name: 'Reset view', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Show starting points', exact: true })).toHaveCount(0);
});

test('every starting point exposes its reviewed focus and applies its own country defaults', async ({ page, request }) => {
  test.setTimeout(180000);
  const metadata = await (await request.get('/api/backend/v1/atlas/presets')).json() as AtlasMetadata;
  for (const preset of metadata.presets) {
    await page.goto('/all');
    const button = page.getByRole('button', { name: preset.name, exact: true });
    await expect(button).toContainText(preset.startingScope);
    await button.click(); await ready(page);
    const params = new URL(page.url()).searchParams;
    expect(params.getAll('country').sort()).toEqual((preset.startingCountries ?? []).slice().sort());
    expect(params.get('country_scope')).toBe(preset.startingCountries?.length ? 'artwork' : null);
    await expect(page.locator('.all-view-context')).toContainText(preset.startingScope);
    await expect(page.locator('.all-lane')).toHaveCount(3);
  }
});

test('switching periods replaces starting countries, preserves manual geography and keeps historical context', async ({ page, request }) => {
  await page.goto('/all');
  await page.getByRole('button', { name: 'The Second World War', exact: true }).click(); await ready(page);
  const broad = await (await request.get('/api/backend/v1/atlas?preset=second-world-war')).json() as AtlasResponse;
  for (const kind of ['book', 'event']) await expect(page.locator(`.all-lane:has(#all-lane-${kind}) > header > span`)).toHaveText(String(broad.lanes.find(lane => lane.key === kind)!.total));
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('radio', { name: 'The Renaissance', exact: true }).check();
  await picker.getByRole('button', { name: 'Done', exact: true }).click(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual(['belgium', 'france', 'germany', 'italy', 'netherlands']);
  await page.getByRole('checkbox', { name: 'Apply countries to books and events too', exact: true }).check(); await ready(page);
  expect(new URL(page.url()).searchParams.has('country_scope')).toBe(false);
  await page.getByRole('button', { name: 'Use full period focus', exact: true }).click(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual([]);
  await page.reload(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual([]);
  await page.getByRole('button', { name: 'Show starting points', exact: true }).click();
  await expect(page.locator('.all-start button')).toHaveCount(30);
});
