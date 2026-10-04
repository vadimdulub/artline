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
  await expect(page.locator('.all-start button')).toHaveCount(32);
  await expect(page.locator('.all-start img')).toHaveCount(32);
  const last = page.getByRole('button', { name: 'The digital turn', exact: true });
  await last.scrollIntoViewIfNeeded();
  const canvas = await page.locator('.all-empty-canvas').boundingBox();
  const button = await last.boundingBox();
  expect(canvas!.y + canvas!.height).toBeGreaterThanOrEqual(button!.y + button!.height);
  await expect(page.locator('.all-empty-canvas')).toHaveCSS('background-color', 'rgb(18, 17, 15)');
  await expect(last).toContainText('Computer art’s documented precedents');
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
    expect(params.getAll('creator').sort()).toEqual((preset.startingCreators ?? []).slice().sort());
    expect(params.get('highlights')).toBe(String(preset.startingHighlights));
    expect(params.get('country_scope')).toBe(preset.startingCountries?.length ? 'artwork' : null);
    await expect(page.locator('.all-view-context')).toContainText(preset.startingScope);
    await expect(page.locator('.all-lane')).toHaveCount(3);
    const artworkImages = page.locator('.all-artwork-lane img');
    await expect(artworkImages.first()).toBeVisible();
    await expect.poll(() => artworkImages.first().evaluate((img: HTMLImageElement) => img.complete && img.naturalWidth > 0)).toBe(true);
  }
});

test('switching periods replaces all recommendations and keeps deliberate clearing after reload', async ({ page, request }) => {
  await page.goto('/all');
  await page.getByRole('button', { name: 'The Second World War', exact: true }).click(); await ready(page);
  const broad = await (await request.get('/api/backend/v1/atlas?preset=second-world-war')).json() as AtlasResponse;
  for (const kind of ['book', 'event']) await expect(page.locator(`.all-lane:has(#all-lane-${kind}) > header > span`)).toHaveText(String(broad.lanes.find(lane => lane.key === kind)!.total));
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('radio', { name: 'The Renaissance', exact: true }).check();
  await picker.getByRole('button', { name: 'Done', exact: true }).click(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('creator')).toEqual([]);
  await expect(page.getByRole('checkbox', { name: 'Highlights', exact: true })).toBeChecked();
  expect(new URL(page.url()).searchParams.getAll('country').sort()).toEqual(['belgium', 'france', 'germany', 'italy', 'netherlands', 'spain', 'united kingdom']);
  await page.locator('.all-view-context > summary').click();
  await page.getByRole('checkbox', { name: 'Apply countries to books and events too', exact: true }).check(); await ready(page);
  expect(new URL(page.url()).searchParams.has('country_scope')).toBe(false);
  await page.getByRole('button', { name: 'Use full period focus', exact: true }).click(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual([]);
  await page.reload(); await ready(page);
  expect(new URL(page.url()).searchParams.getAll('country')).toEqual([]);
  await page.getByRole('button', { name: 'Show starting points', exact: true }).click();
  await expect(page.locator('.all-start button')).toHaveCount(32);
});

for (const width of [1440, 390]) test(`civil rights keeps reviewed creators and compact filters at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/all?preset=civil-rights'); await ready(page);
  await expect(page.locator('.active-filters')).toContainText('28 creators');
  await expect(page.locator('.active-filters')).not.toContainText('Highlights');
  await expect(page.locator('.all-artwork-lane')).not.toContainText('Thomas Weeks Barrett');
  await expect(page.locator('.all-artwork-lane')).toContainText('Horace Pippin');
  expect(await page.locator('.active-filters').evaluate(el => el.getBoundingClientRect().height)).toBeLessThan(150);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: info.outputPath(`civil-rights-${width}.png`), fullPage: true });
  if (width < 760) await page.getByRole('button', { name: 'Filters', exact: true }).click();
  const creators = page.locator('.multi-filter').filter({ has: page.locator('summary[aria-label^="Creators:"]') });
  await creators.locator('summary').click();
  await expect(creators.getByRole('checkbox', { name: 'Faith Ringgold · Painter', exact: true })).toBeChecked();
  await expect(creators.getByRole('checkbox', { name: 'Romare Bearden · Painter', exact: true })).toBeChecked();
  await creators.getByRole('button', { name: 'Clear creators', exact: true }).click();
  await creators.getByRole('button', { name: 'Done', exact: true }).click(); await ready(page);
  await page.reload(); await ready(page);
  expect(new URL(page.url()).searchParams.get('preset_filters')).toBe('custom');
  expect(new URL(page.url()).searchParams.getAll('creator')).toEqual([]);
  await expect(page.locator('.active-filters')).not.toContainText('28 creators');
});
