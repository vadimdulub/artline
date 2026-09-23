import { expect, test } from '@playwright/test';
import type { AtlasResponse } from '../lib/atlas';
import { bookTickPosition } from '../lib/books';

for (const width of [1440, 320]) test(`All fits entries and bars to the interval while the slider retains all years at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 900 });
  const response = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/v1/atlas') && response.ok());
  await page.goto('/all?selection=true&type=artwork&type=book&type=event&start=1400&end=1700&book_top100=true&event_top100=true');
  const data: AtlasResponse = await (await response).json();
  await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false');
  const ticks = await page.locator('.tick-row > span').evaluateAll(nodes => nodes.map(node => ({ label: node.textContent!.trim(), position: parseFloat((node as HTMLElement).style.left) })));
  const first = ticks.find(tick => tick.label === '1400')!, last = ticks.find(tick => tick.label === '1700')!;
  expect(first).toBeDefined(); expect(last).toBeDefined();
  const position = (year: number) => first.position + (year - 1400) / 300 * (last.position - first.position);
  if (width > 760) {
    for (let year = 1400; year <= 1700; year += 100) expect(ticks.find(tick => tick.label === String(year))!.position).toBeCloseTo(position(year), 3);
  }
  const overviewPosition = (year: number) => bookTickPosition(year, data.bounds, 1400);
  await expect(page.getByLabel('Timeline start handle', { exact: true })).toHaveValue(String(Math.round(overviewPosition(1400) * 1000)));
  await expect(page.getByLabel('Timeline end handle', { exact: true })).toHaveValue(String(Math.round(overviewPosition(1700) * 1000)));
  const selectedWidth = await page.getByRole('button', { name: 'Move selected time range', exact: true }).evaluate(node => parseFloat((node as HTMLElement).style.width));
  expect(selectedWidth).toBeCloseTo(overviewPosition(1700) - overviewPosition(1400), 3);
  let marks = 0, bars = 0;
  for (const lane of data.lanes) {
    const section = page.locator(`.all-lane:has(#all-lane-${lane.key})`);
    for (const item of (lane.mode === 'individual' ? lane.items : []).filter(item => item.startYear >= 1400 && item.startYear < 1700).slice(0, 3)) {
      const mark = section.getByRole('button', { name: `${item.title}, ${item.context}, ${item.years}. Open ${lane.singular.toLowerCase()} details`, exact: true });
      expect(await mark.evaluate(node => parseFloat((node as HTMLElement).style.left))).toBeCloseTo(position(item.startYear), 3);
      marks++;
    }
    if (lane.mode === 'density') {
      expect(await section.locator('.period-column').first().evaluate(node => parseFloat((node as HTMLElement).style.getPropertyValue('--column-left')))).toBeCloseTo(position(lane.density[0].start_year), 3);
      bars++;
    }
  }
  expect(marks).toBeGreaterThan(0); expect(bars).toBeGreaterThan(0);
  await page.screenshot({ path: info.outputPath(`all-1400-${width}.png`) });
  await page.getByRole('button', { name: 'Move range 1 year earlier', exact: true }).click();
  await expect(page.getByLabel('All start year', { exact: true })).toHaveValue('1399');
  await expect(page.locator('.timeline-stage')).toHaveAttribute('aria-busy', 'false');
  expect(await page.locator('.tick-row > span').evaluateAll(nodes => nodes.map(node => ({ label: node.textContent!.trim(), position: parseFloat((node as HTMLElement).style.left) })))).not.toEqual(ticks);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
});
