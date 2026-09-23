import { expect, test, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

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
  await expect(picker.getByRole('radio')).toHaveCount(30);
  await picker.getByRole('searchbox', { name: 'Search historical period' }).fill('world war');
  await expect(picker.getByRole('radio')).toHaveCount(3);
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

test('periods combine with existing layer filters and support removal, reload and history', async ({ page }) => {
  await page.goto('/all?selection=true&type=book&country=france&book_language=Q150&book_top100=false&highlights=false&start=1800&end=1950');
  await ready(page);
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('searchbox', { name: 'Search historical period' }).fill('world war');
  await picker.getByRole('radio', { name: 'The First World War', exact: true }).check();
  await picker.getByRole('button', { name: 'Done', exact: true }).click();
  await ready(page);
  const params = new URL(page.url()).searchParams;
  expect(params.getAll('type')).toEqual(['book']);
  expect(params.get('country')).toBe('france');
  expect(params.get('book_language')).toBe('Q150');
  expect(params.get('book_top100')).toBe('false');
  expect(params.get('highlights')).toBe('false');
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1910');
  await expect(page.locator('.all-lane>header h2')).toHaveText(['Books']);
  await page.reload(); await ready(page);
  await expect(picker.locator('summary')).toContainText('The First World War');
  await page.getByRole('button', { name: 'Remove The First World War filter', exact: true }).click();
  await ready(page);
  await expect(picker.locator('summary')).toContainText('All periods');
  await expect(page).not.toHaveURL(/preset=|window=/);
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('-12000');
  await expect(page.locator('.all-lane>header h2')).toHaveText(['Books']);
  await expect(page.getByRole('button', { name: 'Remove France filter', exact: true })).toBeVisible();
  await page.goBack(); await ready(page);
  await expect(picker.locator('summary')).toContainText('The First World War');
  await page.getByRole('button', { name: 'Clear filters', exact: true }).click(); await ready(page);
  await expect(page).not.toHaveURL(/preset=|window=|country=/);
  await expect(page).toHaveURL(/book_language=Q150/);
  await expect(page.locator('.all-lane>header h2')).toHaveText(['Books']);
});

test('clearing a period from its picker restores all years; custom years remain after clearing other filters', async ({ page }) => {
  await page.goto('/all?preset=french-revolution'); await ready(page);
  const picker = page.locator('.all-period-filter .multi-filter');
  await picker.locator('summary').click();
  await picker.getByRole('button', { name: 'Clear historical period', exact: true }).click();
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
