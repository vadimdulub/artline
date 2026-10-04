import { expect, test } from '@playwright/test';

const crowded = '/all?type=book&highlights=false&start=1700&end=2000';

for (const width of [1440, 390]) test(`crowded books show cover, title and date at ${width}`, async ({ page }, info) => {
  await page.setViewportSize({ width, height: 1000 });
  await page.goto(crowded);
  const cards = page.locator('.all-book-card');
  const strip = page.locator('.all-book-strip');
  await expect(cards).toHaveCount(150);
  await expect(page.locator('.all-book-gallery-lane .timeline-overview')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Scroll books right' })).toBeVisible();
  const firstID = await cards.first().getAttribute('data-book-id');
  const title = await cards.first().locator('strong').textContent();
  await expect(cards.first()).toHaveAttribute('title', title!);
  expect(await cards.evaluateAll(nodes => nodes.every(node => {
    const rows = [...node.children].filter(child => !child.classList.contains('all-book-cover'));
    return rows.length === 2 && rows[0].tagName === 'STRONG' && rows[1].tagName === 'TIME';
  }))).toBe(true);
  await expect(cards.locator('.all-book-cover').first()).toBeVisible();
  await expect(page.locator('.all-book-cover img').first()).toHaveAttribute('loading', 'lazy');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  await page.screenshot({ path: info.outputPath(`book-covers-${width}.png`) });
  await cards.first().click();
  await expect(page.getByRole('dialog', { name: 'Book details', exact: true })).toContainText(title!);
  await page.keyboard.press('Escape');
  await expect(cards.first()).toBeFocused();
  for (const last of [300, 450, 600]) {
    await strip.evaluate(el => { el.scrollLeft = el.scrollWidth; });
    await expect(strip.locator('li[aria-posinset]').last()).toHaveAttribute('aria-posinset', String(last));
    await expect(strip).toHaveAttribute('aria-busy', 'false');
  }
  expect(await cards.count()).toBeLessThanOrEqual(450);
  await expect(strip.locator('li[aria-posinset]').first()).toHaveAttribute('aria-posinset', '151');
  await strip.evaluate(el => { el.scrollLeft = 0; });
  await expect(cards.first()).toHaveAttribute('data-book-id', firstID!);
  await expect(cards.first()).toBeInViewport();
  await page.goto('/all?type=book&highlights=true&start=1503&end=1616');
  await expect(page.getByRole('region', { name: 'Books in the combined timeline' })).toBeVisible();
  await expect(page.locator('.all-book-gallery')).toHaveCount(0);
});

test('book gallery keeps loaded cards on failure and retries its cursor', async ({ page }) => {
  await page.goto(crowded);
  const cards = page.locator('.all-book-card');
  const strip = page.locator('.all-book-strip');
  await expect(cards).toHaveCount(150);
  let calls = 0;
  await page.route('**/api/backend/v1/atlas?*', async route => {
    if (!new URL(route.request().url()).searchParams.has('after_book')) return route.continue();
    calls++;
    if (calls === 1) return route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":{"message":"Temporary failure"}}' });
    await route.continue();
  });
  await strip.evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(page.getByText('Couldn’t load more books.', { exact: true })).toBeVisible();
  await expect(cards).toHaveCount(150);
  await page.getByRole('button', { name: 'Try again', exact: true }).click();
  await expect(cards).toHaveCount(300);
  expect(calls).toBe(2);
});

test('book covers fall back safely and paging preserves the other lanes', async ({ page }) => {
  await page.route(/^https:\/\/(upload|thumb)\.wikimedia\.org\//, route => route.abort());
  await page.goto(crowded + '&type=artwork&type=event');
  const cards = page.locator('.all-book-card');
  await expect(cards).toHaveCount(150);
  await expect(page.locator('.all-artwork-card')).toHaveCount(150);
  const firstArtwork = await page.locator('.all-artwork-card').first().getAttribute('data-artwork-id');
  const covered = cards.filter({ has: page.locator('.all-book-cover img') }).first();
  // Offscreen covers remain lazy; scrolling to one triggers the failed request.
  const coveredID = await covered.getAttribute('data-book-id');
  await covered.scrollIntoViewIfNeeded();
  await expect(page.locator(`.all-book-card[data-book-id="${coveredID}"]`).getByRole('img', { name: 'Cover unavailable' })).toBeVisible();
  await page.locator('.all-book-strip').evaluate(el => { el.scrollLeft = el.scrollWidth; });
  await expect(cards).toHaveCount(300);
  await expect(page.locator('.all-artwork-card')).toHaveCount(150);
  await expect(page.locator('.all-artwork-card').first()).toHaveAttribute('data-artwork-id', firstArtwork!);
  await expect(page.locator('.all-lane')).toHaveCount(3);
});
