import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.beforeEach(async ({ page }) => {
  if (process.env.ARTLINE_PERIODS_API) await page.route('**/api/backend/v1/**', async route => {
    const url = new URL(route.request().url());
    await route.fulfill({ response: await route.fetch({ url: process.env.ARTLINE_PERIODS_API + url.pathname.replace('/api/backend/v1', '/api/v1') + url.search }) });
  });
});

async function ready(page: Page) {
  await expect(page.locator('.all-explorer .timeline-stage')).toHaveAttribute('aria-busy', 'false', { timeout: 20000 });
  await expect(page.locator('.all-explorer').getByRole('alert')).toHaveCount(0);
}

for (const width of [1440, 390, 320]) test(`historical period picker is searchable and accessible at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('/all');
  if (width < 760) await page.getByRole('button', { name: 'Filters', exact: true }).click();
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await expect(picker.getByRole('radio')).toHaveCount(32);
  await picker.getByRole('searchbox', { name: 'Search period or theme' }).fill('world war');
  await expect(picker.getByRole('radio', { name: 'The First World War', exact: true })).toBeVisible();
  await expect(picker.getByRole('radio', { name: 'The Second World War', exact: true })).toBeVisible();
  await picker.getByRole('radio', { name: 'The First World War', exact: true }).check();
  await ready(page);
  await expect(page.getByRole('button', { name: 'Remove The First World War filter', exact: true })).toBeVisible();
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await picker.getByRole('radio', { name: 'The Second World War', exact: true }).check();
  await ready(page);
  await expect(picker.locator('input:checked')).toHaveCount(1);
  await expect(page.getByRole('button', { name: 'Remove The First World War filter', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Remove The Second World War filter', exact: true })).toBeVisible();
  const bounds = (await picker.locator('.multi-filter-panel').boundingBox())!;
  expect(bounds.x).toBeGreaterThanOrEqual(0);
  expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
  expect(bounds.y + bounds.height).toBeLessThanOrEqual(900);
  expect((await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze()).violations).toEqual([]);
  await page.screenshot({ path: info.outputPath(`period-picker-${width}.png`) });
  await page.keyboard.press('Escape');
  await expect(picker).not.toHaveAttribute('open');
  await expect(picker.locator('summary')).toBeFocused();
  if (width < 760) await expect(page.getByRole('button', { name: 'Filters', exact: true })).toHaveAttribute('aria-expanded', 'true');
});

test('clearing a period from its picker restores all years; custom years remain after clearing other filters', async ({ page }) => {
  await page.goto('/all?preset=french-revolution'); await ready(page);
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('button', { name: 'Clear period or theme', exact: true }).click();
  await picker.getByRole('button', { name: 'Done', exact: true }).click();
  await ready(page);
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('-12000');
  await page.getByLabel('All start year', { exact: true }).fill('1800');
  await page.getByLabel('All end year', { exact: true }).fill('1900');
  await page.getByLabel('All end year', { exact: true }).press('Enter'); await ready(page);
  await page.getByRole('checkbox', { name: 'Highlights', exact: true }).check(); await ready(page);
  await page.getByRole('button', { name: 'Clear filters', exact: true }).click(); await ready(page);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1800');
  await expect(page.getByLabel('All end year', { exact: true })).toHaveValue('1900');
});


test('period search includes place, dates and scope; selection survives reload and history', async ({ page }) => {
  await page.goto('/all');
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await expect(picker.getByRole('group', { name: 'Connected worlds', exact: true })).toBeVisible();
  await picker.getByRole('searchbox').fill('Timbuktu');
  await expect(picker.getByRole('radio', { name: 'West African trade and learning', exact: true })).toBeVisible();
  await picker.getByRole('searchbox').fill('1600–1750');
  await expect(picker.getByRole('radio', { name: 'Baroque art and its world', exact: true })).toBeVisible();
  await picker.getByRole('radio', { name: 'Baroque art and its world', exact: true }).check();
  await picker.getByRole('button', { name: 'Done', exact: true }).click();
  await ready(page);
  await expect(page).toHaveURL(/preset=baroque/);
  await expect(page.getByRole('checkbox', { name: 'Highlights', exact: true })).not.toBeChecked();
  await expect(page.locator('.all-lane')).toHaveCount(3);
  await expect(page.locator('.all-lane').filter({ has: page.getByRole('button', { name: 'Books', exact: true }) })).toContainText('Paradise Lost');
  await page.reload(); await ready(page);
  await expect(picker.locator('summary')).toContainText('Baroque art and its world');
  await page.getByRole('button', { name: 'Remove Baroque art and its world filter', exact: true }).click();
  await ready(page);
  await expect(page).not.toHaveURL(/preset=/);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('-12000');
  await page.goBack(); await ready(page);
  await expect(page).toHaveURL(/preset=baroque/);
});

test('clear filters removes lane filters and preserves manual years and layers', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&book_language=Q150&event_kind=war&artwork_movement=romanticism&highlights=false&start=1800&end=1900');
  await ready(page);
  for (const label of ['Books: 1 filter', 'Artworks: 1 filter', 'Events: 1 filter']) {
    await expect(page.getByRole('button', { name: `Remove ${label} filter`, exact: true })).toBeVisible();
  }
  await page.getByRole('button', { name: 'Clear filters', exact: true }).click();
  await ready(page);
  await expect(page).not.toHaveURL(/book_language|event_kind|artwork_movement/);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1800');
  await expect(page.getByLabel('All end year', { exact: true })).toHaveValue('1900');
  await expect(page.locator('.all-lane>header h2')).toHaveText(['Books']);
  await expect(page.getByRole('button', { name: 'Clear filters', exact: true })).toHaveCount(0);
});
